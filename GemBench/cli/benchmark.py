import argparse
import json
import sys
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..benchmarking.tools.ModelPrice import ModelPricing
from .common import (
    add_check,
    add_env_check,
    add_matrix_args,
    non_negative_int,
    positive_int,
    print_dict_rows,
)
from .constants import (
    ALL_DATASETS,
    ALL_MATRICES,
    CHAT_DATASETS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_JUDGE_MODEL,
    DEFAULT_MODEL,
    METHOD_ALIASES,
    METHODS,
    QUAL_MATRICES,
    QUANT_MATRICES,
    SEARCH_DATASET,
    SELECT_MATRICES,
)


class DatasetsCommand:
    """Command group for bundled dataset inspection."""

    def add_to(self, subparsers: Any) -> None:
        """Register dataset inspection subcommands."""
        parser = subparsers.add_parser(
            "datasets",
            help="Inspect bundled datasets.",
        )
        parser.set_defaults(handler=self.handle)
        command_parsers = parser.add_subparsers(
            dest="datasets_command",
            required=True,
        )
        list_parser = command_parsers.add_parser(
            "list",
            help="List supported datasets.",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="Print datasets as JSON.",
        )

    def handle(self, args) -> int:
        """Execute the selected datasets command."""
        if args.datasets_command != "list":
            raise ValueError(f"unknown datasets command: {args.datasets_command}")

        datasets = [
            {
                "name": "MT-Human",
                "task": "chatbot",
                "description": "Humanities questions from MT-Bench.",
            },
            {
                "name": "LM-Market",
                "task": "chatbot",
                "description": "Marketing-oriented LMSYS-Chat-1M queries.",
            },
            {
                "name": "CA_Prod",
                "task": "search",
                "description": "Commercial search queries with candidate products.",
            },
        ]
        if args.json:
            print(json.dumps(datasets, indent=2))
        else:
            print_dict_rows(datasets, ["name", "task", "description"])
        return 0


class GenerateCommand:
    """Command for generating benchmark outputs without evaluation."""

    def add_to(self, subparsers: Any) -> None:
        """Register benchmark generation arguments."""
        parser = subparsers.add_parser(
            "generate",
            help="Run baseline methods to generate ad-injected responses.",
        )
        add_benchmark_args(parser)
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Run configured baselines and write results.json."""
        benchmark = build_benchmark(args)
        benchmark.process_results()
        print(f"results: {Path(benchmark.output_dir) / 'results.json'}")
        return 0


class RunCommand:
    """Command for full benchmark generation and evaluation."""

    def add_to(self, subparsers: Any) -> None:
        """Register full benchmark run arguments."""
        parser = subparsers.add_parser(
            "run",
            help="Generate ad-injected responses, evaluate them, and write reports.",
        )
        add_benchmark_args(parser)
        add_matrix_args(parser, ALL_MATRICES)
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Run generation, evaluation, and report export."""
        benchmark = build_benchmark(args)
        benchmark.run(evaluate_matrix=resolve_matrices(args.matrix))
        print(f"results: {Path(benchmark.output_dir) / 'results.json'}")
        print(f"evaluation: {Path(benchmark.output_dir) / 'evaluation_result.json'}")
        return 0


class EvaluateCommand:
    """Command for evaluating an existing benchmark result file."""

    def add_to(self, subparsers: Any) -> None:
        """Register standalone evaluation arguments."""
        parser = subparsers.add_parser(
            "evaluate",
            help="Evaluate an existing results.json file.",
        )
        parser.add_argument(
            "results",
            help="Path to results.json or an output directory containing results.json.",
        )
        parser.add_argument(
            "--output-dir",
            help="Directory for evaluation outputs. Defaults to the results directory.",
        )
        parser.add_argument(
            "--judge-model",
            default=DEFAULT_JUDGE_MODEL,
            help=f"Judge model for qualitative evaluation. Defaults to {DEFAULT_JUDGE_MODEL}.",
        )
        parser.add_argument(
            "--no-report",
            action="store_true",
            help="Only write evaluation_result.json, not Excel report files.",
        )
        add_matrix_args(parser, ALL_MATRICES)
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Evaluate an existing results.json file."""
        results_path = resolve_results_path(args.results)
        output_dir = Path(args.output_dir).expanduser() if args.output_dir else results_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        from ..benchmarking.utils.struct import SolutionResult

        results = SolutionResult.load(str(results_path))
        evaluation_result = evaluate_results(
            results=results,
            output_dir=output_dir,
            judge_model=args.judge_model,
            matrixes=resolve_matrices(args.matrix),
            report=not args.no_report,
        )
        print(f"evaluation: {output_dir / 'evaluation_result.json'}")
        print(f"records: {len(evaluation_result)}")
        return 0


class DiagnoseCommand:
    """Command for local environment and benchmark readiness checks."""

    def add_to(self, subparsers: Any) -> None:
        """Register diagnostic command arguments."""
        parser = subparsers.add_parser(
            "diagnose",
            help="Check environment, datasets, pricing, and CLI readiness.",
        )
        parser.add_argument(
            "--model-name",
            default=DEFAULT_MODEL,
            help=f"Generation model to check. Defaults to {DEFAULT_MODEL}.",
        )
        parser.add_argument(
            "--embedding-model",
            default=DEFAULT_EMBEDDING_MODEL,
            help=f"Embedding model to check. Defaults to {DEFAULT_EMBEDDING_MODEL}.",
        )
        parser.add_argument(
            "--judge-model",
            default=DEFAULT_JUDGE_MODEL,
            help=f"Judge model to check. Defaults to {DEFAULT_JUDGE_MODEL}.",
        )
        parser.add_argument(
            "--price-file",
            help="Custom price JSON path to check.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print diagnostics as JSON.",
        )
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Run environment, pricing, dataset, and baseline checks."""
        pricing = ModelPricing(price_file=args.price_file)
        price_file = pricing._price_file_path(args.price_file)
        checks = []

        add_check(
            checks,
            "package_import",
            "ok",
            "GemBench package import succeeded.",
        )
        add_env_check(checks, "OPENAI_API_KEY")
        add_env_check(checks, "BASE_URL")
        add_env_check(checks, "EMBEDDING_API_KEY", fallback="OPENAI_API_KEY")
        add_env_check(checks, "EMBEDDING_BASE_URL", fallback="BASE_URL")
        add_env_check(checks, "JUDGE_API_KEY", fallback="OPENAI_API_KEY")
        add_env_check(checks, "JUDGE_BASE_URL", fallback="BASE_URL")
        add_check(
            checks,
            "custom_price_file",
            "ok" if price_file.exists() else "warning",
            str(price_file) if price_file.exists() else f"{price_file} does not exist yet.",
        )

        for model in [args.model_name, args.embedding_model, args.judge_model]:
            status = "ok" if pricing.has_price(model) else "warning"
            detail = "configured" if status == "ok" else "missing; runtime price will be 0"
            add_check(checks, f"price:{model}", status, detail)

        for dataset in dataset_diagnostics():
            add_check(
                checks,
                f"dataset:{dataset['name']}",
                "ok",
                f"{dataset['count']} samples for {dataset['task']} task",
            )

        for key, value in METHODS.items():
            add_check(
                checks,
                f"baseline:{key}",
                "ok",
                f"{value['name']} supports {', '.join(value['tasks'])}",
            )

        if args.json:
            print(json.dumps(checks, indent=2))
        else:
            print_dict_rows(checks, ["name", "status", "detail"])

        return 1 if any(item["status"] == "error" for item in checks) else 0


def add_benchmark_args(parser: argparse.ArgumentParser) -> None:
    """Add shared benchmark execution arguments."""
    parser.add_argument(
        "-b",
        "--baseline",
        action="append",
        help=(
            "Baseline to run. Repeat or comma-separate values. "
            "Use all for every built-in baseline. Defaults to ad-chat."
        ),
    )
    parser.add_argument(
        "-d",
        "--dataset",
        action="append",
        choices=ALL_DATASETS,
        help=(
            "Dataset to run. Repeat for multiple datasets. "
            "Defaults to MT-Human and LM-Market."
        ),
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL,
        help=f"Generation model. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Embedding model. Defaults to {DEFAULT_EMBEDDING_MODEL}.",
    )
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Judge model. Defaults to {DEFAULT_JUDGE_MODEL}.",
    )
    parser.add_argument(
        "--score-func",
        choices=["linear", "log"],
        default="linear",
        help="Ad-LLM score function. Defaults to linear.",
    )
    parser.add_argument(
        "--rag-top-k",
        type=positive_int,
        default=5,
        help="Top-k products for RAG-AdChat retrieval. Defaults to 5.",
    )
    parser.add_argument(
        "--repeats",
        type=positive_int,
        default=1,
        help="Number of repeats. Defaults to 1.",
    )
    parser.add_argument(
        "--max-samples",
        type=non_negative_int,
        default=0,
        help="Maximum samples per dataset. Defaults to all samples.",
    )
    parser.add_argument(
        "--output-dir",
        help="Base output directory. Defaults to GemBench/benchmarking.",
    )
    parser.add_argument(
        "--tag",
        help="Output run tag. Defaults to a tag derived from selected options.",
    )


def build_benchmark(args):
    """Create a GemBench runner from parsed CLI arguments."""
    from ..benchmarking import GemBench

    baselines = resolve_baselines(args.baseline)
    data_sets = resolve_data_sets(args.dataset)
    chat_data_sets = [data_set for data_set in data_sets if data_set != SEARCH_DATASET]
    use_search = SEARCH_DATASET in data_sets
    all_solutions, all_selectors = build_baseline_callables(args, baselines)
    solutions = {
        name: fn
        for name, fn in all_solutions.items()
        if chat_data_sets
    }
    selectors = {
        name: fn
        for name, fn in all_selectors.items()
        if use_search
    }
    if not solutions and not selectors:
        raise ValueError("no generation or selection task selected")

    output_dir = args.output_dir or GemBench.current_dir
    tag = args.tag or default_tag(baselines, data_sets, args)
    return GemBench(
        solutions=solutions,
        data_sets=chat_data_sets,
        best_product_selector=selectors,
        judge_model=args.judge_model,
        output_dir=output_dir,
        n_repeats=args.repeats,
        max_samples=args.max_samples,
        tags=tag,
    )


def build_baseline_callables(args, baselines: List[str]):
    """Build solution and selector callables for selected baselines."""
    from .. import (
        AdChatWorkflow,
        AdLLMWorkflow,
        LINEAR_WEIGHT,
        LOG_WEIGHT,
        PRODUCT_DATASET_PATH,
        RAGAdChatWorkflow,
        TOPIC_DATASET_PATH,
    )

    solutions = {}
    selectors = {}
    adchat_workflow = None
    adllm_workflow = None
    rag_adchat_workflow = None

    if "ad-chat" in baselines:
        adchat_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name=args.model_name,
        )
        solutions["Ad-Chat"] = partial(
            adchat_workflow.run,
            solution_name="chi",
        )
        selectors["Ad-Chat"] = partial(
            adchat_workflow.get_best_product,
            solution_name="chi",
        )

    adllm_baselines = [name for name in baselines if name in {"gi-r", "gir-r", "gir-p"}]
    if adllm_baselines:
        score_func = LINEAR_WEIGHT if args.score_func == "linear" else LOG_WEIGHT
        adllm_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model=args.embedding_model,
            model_name=args.model_name,
            score_func=score_func,
        )

    if "gi-r" in baselines:
        solutions["GI-R"] = partial(
            adllm_workflow.run,
            query_type="QUERY_RESPONSE",
            solution_name="BASIC_GEN_INSERT",
        )
        selectors["GI-R"] = partial(
            adllm_workflow.run,
            query_type="QUERY_RESPONSE",
            solution_name="BASIC_GEN_INSERT",
        )
    if "gir-r" in baselines:
        solutions["GIR-R"] = partial(
            adllm_workflow.run,
            query_type="QUERY_RESPONSE",
            solution_name="REFINE_GEN_INSERT",
        )
        selectors["GIR-R"] = partial(
            adllm_workflow.run,
            query_type="QUERY_RESPONSE",
            solution_name="REFINE_GEN_INSERT",
        )
    if "gir-p" in baselines:
        solutions["GIR-P"] = partial(
            adllm_workflow.run,
            query_type="QUERY_PROMPT",
            solution_name="REFINE_GEN_INSERT",
        )
        selectors["GIR-P"] = partial(
            adllm_workflow.run,
            query_type="QUERY_PROMPT",
            solution_name="REFINE_GEN_INSERT",
        )

    if "rag-adchat" in baselines:
        rag_adchat_workflow = RAGAdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name=args.model_name,
            rag_model=args.embedding_model,
            top_k=args.rag_top_k,
        )
        solutions["RAG-AdChat"] = rag_adchat_workflow.run
        selectors["RAG-AdChat"] = rag_adchat_workflow.get_best_product

    return solutions, selectors


def evaluate_results(
    results,
    output_dir: Path,
    judge_model: str,
    matrixes: Optional[List[str]],
    report: bool,
):
    """Evaluate a SolutionResult with selected matrixes."""
    from ..benchmarking.evaluator import LAJQualitativeEvaluator, QuantEvaluator
    from ..benchmarking.evaluator.selector_evaluator import SelectEvaluator
    from ..benchmarking.utils.struct import EvaluationResult

    selected_matrixes = matrixes or default_matrixes_for_results(results)
    unknown = [matrix for matrix in selected_matrixes if matrix not in ALL_MATRICES]
    if unknown:
        raise ValueError(f"unknown evaluation matrix: {', '.join(unknown)}")

    evaluation_result = EvaluationResult()
    quant_matrixes = [matrix for matrix in selected_matrixes if matrix in QUANT_MATRICES]
    qual_matrixes = [matrix for matrix in selected_matrixes if matrix in QUAL_MATRICES]
    select_matrixes = [matrix for matrix in selected_matrixes if matrix in SELECT_MATRICES]

    if quant_matrixes:
        evaluator = QuantEvaluator(output_dir=str(output_dir), results=results)
        evaluation_result += evaluator.evaluate(quant_matrixes)
    if qual_matrixes:
        evaluator = LAJQualitativeEvaluator(
            output_dir=str(output_dir),
            results=results,
            judge_model=judge_model,
        )
        evaluation_result += evaluator.evaluate(qual_matrixes)
    if select_matrixes:
        select_results = results.query_result_by_attr({"dataSet": [SEARCH_DATASET]})
        if len(select_results) == 0:
            print(
                "warning: product_selection_accuracy requested but no CA_Prod results found",
                file=sys.stderr,
            )
        else:
            evaluator = SelectEvaluator(
                output_dir=str(output_dir),
                best_product_selectors={},
                results=select_results,
            )
            evaluation_result += evaluator.evaluate(select_matrixes)

    evaluation_result.save(str(output_dir / "evaluation_result.json"))
    if report:
        write_reports(evaluation_result, output_dir)
    return evaluation_result


def write_reports(evaluation_result, output_dir: Path) -> None:
    """Write standard Excel evaluation reports."""
    evaluation_result.save_to_excel_report(
        str(output_dir / "evaluation_result.xlsx"),
        title="Report",
    )
    evaluation_result.average_by_batch().save_to_excel_report(
        str(output_dir / "evaluation_result_average.xlsx"),
        title="Report_average",
    )
    result_with_product = evaluation_result.fliter_only_has_product()
    result_with_product.save_to_excel_report(
        str(output_dir / "evaluation_result_with_product.xlsx"),
        title="Report_with_product",
    )
    result_with_product.average_by_batch().save_to_excel_report(
        str(output_dir / "evaluation_result_with_product_average.xlsx"),
        title="Report_with_product_average",
    )


def default_matrixes_for_results(results) -> List[str]:
    """Choose default matrixes based on datasets in a result file."""
    matrixes = QUANT_MATRICES + QUAL_MATRICES
    if SEARCH_DATASET in results.get_keys_by_attr("dataSet"):
        matrixes += SELECT_MATRICES
    return matrixes


def resolve_baselines(values: Optional[List[str]]) -> List[str]:
    """Resolve baseline CLI values and aliases to canonical keys."""
    if not values:
        return ["ad-chat"]

    resolved = []
    for value in values:
        for item in value.split(","):
            key = item.strip().lower()
            if not key:
                continue
            alias = METHOD_ALIASES.get(key)
            if alias is None:
                raise ValueError(f"unknown baseline: {item}")
            if alias == "all":
                return list(METHODS.keys())
            if alias not in resolved:
                resolved.append(alias)
    return resolved or ["ad-chat"]


def resolve_data_sets(values: Optional[List[str]]) -> List[str]:
    """Resolve dataset CLI values to supported dataset names."""
    if not values:
        return CHAT_DATASETS[:]

    resolved = []
    for value in values:
        for item in value.split(","):
            data_set = item.strip()
            if not data_set:
                continue
            if data_set not in ALL_DATASETS:
                raise ValueError(f"unknown dataset: {item}")
            if data_set not in resolved:
                resolved.append(data_set)
    return resolved


def resolve_matrices(values: Optional[List[str]]) -> Optional[List[str]]:
    """Resolve repeated or comma-separated matrix arguments."""
    if not values:
        return None

    matrixes = []
    for value in values:
        for item in value.split(","):
            matrix = item.strip()
            if matrix and matrix not in matrixes:
                matrixes.append(matrix)
    return matrixes or None


def resolve_results_path(value: str) -> Path:
    """Resolve a results path or output directory to results.json."""
    path = Path(value).expanduser()
    if path.is_dir():
        path = path / "results.json"
    if not path.exists():
        raise ValueError(f"results file not found: {path}")
    return path


def default_tag(baselines: List[str], data_sets: List[str], args) -> str:
    """Build the default benchmark output tag."""
    sample_tag = f"max-{args.max_samples}" if args.max_samples else "all"
    return (
        f"{'-'.join(data_sets)}-"
        f"{'-'.join(baselines)}-"
        f"{args.embedding_model}-"
        f"{args.model_name}-"
        f"repeat-{args.repeats}-"
        f"{sample_tag}"
    )


def dataset_diagnostics() -> List[Dict[str, Any]]:
    """Collect dataset counts for the diagnose command."""
    from ..benchmarking.dataset import GemDatasets

    datasets = GemDatasets()
    rows = []
    for name in CHAT_DATASETS:
        rows.append(
            {
                "name": name,
                "task": "chatbot",
                "count": len(datasets.get_prompt_list(name)),
            }
        )

    problem_product_list, _query_clusters = datasets.build_query_candidate_product_list()
    rows.append(
        {
            "name": SEARCH_DATASET,
            "task": "search",
            "count": len(problem_product_list),
        }
    )
    return rows
