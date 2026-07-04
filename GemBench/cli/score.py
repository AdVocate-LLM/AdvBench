import json
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..benchmarking.evaluator.laaj_evaluator import LAJQualitativeEvaluator
from ..benchmarking.evaluator.quantitative_evaluator.quant_metrics import (
    evaluate_ad_content_alignment,
    evaluate_ad_transition_similarity,
    evaluate_global_coherence,
    evaluate_local_flow,
)
from ..benchmarking.utils.result import Result
from ..benchmarking.utils.struct import EvaluationResult, SolutionResult
from .benchmark import write_reports
from .common import add_matrix_args, print_dict_rows
from .constants import (
    DEFAULT_JUDGE_MODEL,
    QUAL_MATRICES,
    QUANT_MATRICES,
    SELECT_MATRICES,
)


DEFAULT_SCORE_MATRICES = ["has_ad", "in_token", "out_token", "price"]
SEMANTIC_SCORE_MATRICES = [
    "local_flow",
    "global_coherence",
    "ad_transition_similarity",
    "ad_content_alignment",
]
ALL_SCORE_MATRICES = QUANT_MATRICES + QUAL_MATRICES


class ScoreCommand:
    """Command for scoring production inject outputs."""

    def add_to(self, subparsers: Any) -> None:
        """Register score command arguments."""
        parser = subparsers.add_parser(
            "score",
            help="Score inject results from external queries.",
        )
        parser.add_argument(
            "results",
            help="JSON or JSONL file produced by gembench inject.",
        )
        parser.add_argument(
            "--output",
            help="Write production score JSON to this path. Defaults to stdout summary.",
        )
        parser.add_argument(
            "--output-dir",
            help="Directory for raw evaluation_result.json and optional Excel reports.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print production score JSON to stdout.",
        )
        parser.add_argument(
            "--jsonl",
            action="store_true",
            help="Write one score row per line instead of a JSON object.",
        )
        parser.add_argument(
            "--report",
            action="store_true",
            help="Also write Excel reports under --output-dir.",
        )
        parser.add_argument(
            "--judge-model",
            default=DEFAULT_JUDGE_MODEL,
            help=f"Judge model for qualitative evaluation. Defaults to {DEFAULT_JUDGE_MODEL}.",
        )
        add_matrix_args(parser, ALL_SCORE_MATRICES)
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Score an inject output file and emit production-shaped results."""
        records = load_score_records(args.results)
        matrixes = resolve_score_matrices(args.matrix)
        solution_result = records_to_solution_result(records)
        output_dir = resolve_output_dir(args.results, args.output_dir, args.report)
        evaluation_result = score_solution_result(
            results=solution_result,
            matrixes=matrixes,
            judge_model=args.judge_model,
            output_dir=output_dir,
            report=args.report,
        )
        payload = build_score_payload(evaluation_result)
        write_score_payload(payload, args.output, args.json, args.jsonl)
        return 0


def load_score_records(results_file: str) -> List[Dict[str, Any]]:
    """Load inject result records from JSON or JSONL."""
    path = Path(results_file).expanduser()
    if not path.exists():
        raise ValueError(f"score input not found: {path}")

    if path.suffix.lower() == ".jsonl":
        records = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return validate_score_records(records)

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        data = data["records"]
    if isinstance(data, dict):
        data = [data]
    return validate_score_records(data)


def validate_score_records(records: Any) -> List[Dict[str, Any]]:
    """Validate that loaded score input is a list of objects."""
    if not isinstance(records, list):
        raise ValueError("score input must be a JSON object, JSON array, or JSONL file")
    invalid = [index for index, record in enumerate(records) if not isinstance(record, dict)]
    if invalid:
        raise ValueError(f"score input contains non-object records: {invalid}")
    if not records:
        raise ValueError("score input does not contain any records")
    return records


def records_to_solution_result(records: List[Dict[str, Any]]) -> SolutionResult:
    """Convert inject records to the benchmark scoring structure."""
    solution_result = SolutionResult()
    for record in records:
        query = record.get("query") or record.get("prompt") or record.get("question")
        answer = record.get("answer") or record.get("response") or record.get("content")
        if not query:
            raise ValueError(f"score record is missing query/prompt/question: {record}")
        if answer is None:
            raise ValueError(f"score record is missing answer/response/content: {record}")

        product = normalize_score_product(record.get("product"))
        method = (
            record.get("method")
            or record.get("solution")
            or record.get("solution_name")
            or "external"
        )
        repeat_id = str(record.get("repeat_id") or record.get("batch") or 0)
        category = record.get("category") or product.get("category") or "external"
        result = Result(
            prompt=str(query),
            category=str(category),
            solution_tag=str(method),
            raw_content=str(answer),
            product=product,
            price=normalize_score_price(record.get("price")),
        )
        solution_result.add_result(str(method), "External", repeat_id, result)
    return solution_result


def normalize_score_product(product: Any) -> Dict[str, Any]:
    """Normalize product metadata for scoring metrics."""
    empty_product = {
        "name": None,
        "description": None,
        "desc": None,
        "category": None,
        "url": None,
    }
    if product is None:
        return empty_product
    if isinstance(product, str):
        normalized = empty_product.copy()
        normalized["name"] = product or None
        return normalized
    if not isinstance(product, dict):
        return empty_product

    normalized = dict(product)
    description = normalized.get("description") or normalized.get("desc")
    normalized["name"] = normalized.get("name") or normalized.get("title")
    normalized["description"] = description
    normalized["desc"] = description
    normalized["category"] = normalized.get("category")
    normalized["url"] = normalized.get("url") or normalized.get("link")
    return normalized


def normalize_score_price(price: Any) -> Dict[str, float]:
    """Normalize token and price accounting for scoring."""
    if not isinstance(price, dict):
        price = {}
    return {
        "in_token": float(price.get("in_token", 0) or 0),
        "out_token": float(price.get("out_token", 0) or 0),
        "price": float(price.get("price", 0) or 0),
    }


def resolve_score_matrices(values: Optional[List[str]]) -> List[str]:
    """Resolve score matrix arguments and defaults."""
    if not values:
        return DEFAULT_SCORE_MATRICES[:]

    matrixes = []
    for value in values:
        for item in value.split(","):
            matrix = item.strip()
            if not matrix:
                continue
            if matrix == "all":
                return ALL_SCORE_MATRICES[:]
            if matrix in SELECT_MATRICES:
                raise ValueError(f"{matrix} is only supported for benchmark search results")
            if matrix not in ALL_SCORE_MATRICES:
                raise ValueError(f"unknown score matrix: {matrix}")
            if matrix not in matrixes:
                matrixes.append(matrix)
    return matrixes or DEFAULT_SCORE_MATRICES[:]


def resolve_output_dir(
    results_file: str,
    output_dir: Optional[str],
    report: bool,
) -> Optional[Path]:
    """Resolve the optional directory for raw scoring artifacts."""
    if output_dir:
        path = Path(output_dir).expanduser()
    elif report:
        path = Path(results_file).expanduser().parent / "score_output"
    else:
        return None
    path.mkdir(parents=True, exist_ok=True)
    return path


def score_solution_result(
    results: SolutionResult,
    matrixes: List[str],
    judge_model: str,
    output_dir: Optional[Path],
    report: bool,
) -> EvaluationResult:
    """Score a SolutionResult with production-supported matrixes."""
    if any(matrix in SEMANTIC_SCORE_MATRICES for matrix in matrixes):
        results.embedding_all_results()

    evaluation_result = EvaluationResult()
    quant_matrixes = [matrix for matrix in matrixes if matrix in QUANT_MATRICES]
    qual_matrixes = [matrix for matrix in matrixes if matrix in QUAL_MATRICES]

    for matrix in quant_matrixes:
        evaluation_result += results.self_evaluated_with_matrix_by_fn(
            evaluator_fn=partial(score_quant_metric, matrix),
            eval_matrix_label=matrix,
        )

    if qual_matrixes:
        evaluator = LAJQualitativeEvaluator(
            output_dir=str(output_dir) if output_dir else "",
            results=results,
            judge_model=judge_model,
        )
        evaluation_result += evaluator.evaluate(
            analysis_matrixes=qual_matrixes,
            is_saved=output_dir is not None,
        )

    if output_dir:
        evaluation_result.save(str(output_dir / "evaluation_result.json"))
        if report:
            write_reports(evaluation_result, output_dir)
    return evaluation_result


def score_quant_metric(matrix_name: str, response: Result) -> Optional[float]:
    """Calculate one quantitative production score."""
    if matrix_name == "has_ad":
        product = response.get_product()
        return 100 if product is not None and product.get("name") is not None else 0
    if matrix_name == "local_flow":
        return evaluate_local_flow(response.get_adjacent_sentence_similarities())
    if matrix_name == "global_coherence":
        return evaluate_global_coherence(response.get_sentences())
    if matrix_name == "ad_transition_similarity":
        return evaluate_ad_transition_similarity(
            response.get_adjacent_sentence_similarities(),
            response.get_ad_indices(),
        )
    if matrix_name == "ad_content_alignment":
        return evaluate_ad_content_alignment(
            response.get_sentences(),
            response.get_ad_indices(),
        )
    if matrix_name == "in_token":
        return response.get_price()["in_token"]
    if matrix_name == "out_token":
        return response.get_price()["out_token"]
    if matrix_name == "price":
        return response.get_price()["price"]
    raise ValueError(f"unknown quantitative score matrix: {matrix_name}")


def build_score_payload(evaluation_result: EvaluationResult) -> Dict[str, Any]:
    """Build production score output with summary and rows."""
    scores = score_rows(evaluation_result)
    return {
        "summary": score_summary_rows(scores),
        "scores": scores,
    }


def score_rows(evaluation_result: EvaluationResult) -> List[Dict[str, Any]]:
    """Convert EvaluationResult entries to row dictionaries."""
    rows = []
    for key, score in evaluation_result:
        rows.append(
            {
                "method": key[0],
                "dataset": key[1],
                "repeat_id": key[2],
                "matrix": key[3],
                "category": key[4],
                "query": key[5],
                "answer": key[6][0],
                "product": key[6][1],
                "score": score,
            }
        )
    return rows


def score_summary_rows(scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate score rows by method and matrix."""
    grouped = {}
    for row in scores:
        key = (row["method"], row["matrix"])
        grouped.setdefault(key, []).append(float(row["score"]))

    summary = []
    for (method, matrix), values in sorted(grouped.items()):
        summary.append(
            {
                "method": method,
                "matrix": matrix,
                "count": len(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
        )
    return summary


def write_score_payload(
    payload: Dict[str, Any],
    output: Optional[str],
    json_output: bool,
    jsonl: bool,
) -> None:
    """Write score payload to stdout or a file."""
    if jsonl:
        content = "\n".join(
            json.dumps(row, ensure_ascii=False)
            for row in payload["scores"]
        )
        if content:
            content += "\n"
    elif output or json_output:
        content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        print_dict_rows(format_summary_for_table(payload["summary"]), [
            "method",
            "matrix",
            "count",
            "average",
            "min",
            "max",
        ])
        return

    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


def format_summary_for_table(summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format numeric summary values for text table output."""
    rows = []
    for row in summary:
        rows.append(
            {
                "method": row["method"],
                "matrix": row["matrix"],
                "count": row["count"],
                "average": f"{row['average']:.6g}",
                "min": f"{row['min']:.6g}",
                "max": f"{row['max']:.6g}",
            }
        )
    return rows
