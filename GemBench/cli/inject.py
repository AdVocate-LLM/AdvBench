import json
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ads import (
    load_ad_records,
    remove_temp_file,
    write_temp_ad_file,
    write_temp_topic_file,
)
from .common import positive_int, write_json_records
from .constants import DEFAULT_EMBEDDING_MODEL, DEFAULT_MODEL


class InjectCommand:
    """Command for production-style ad injection over external queries."""

    def add_to(self, subparsers) -> None:
        """Register the inject command arguments."""
        parser = subparsers.add_parser(
            "inject",
            help="Generate ad-injected responses for external queries.",
        )
        parser.add_argument(
            "-q",
            "--query",
            action="append",
            help="User query. Repeat for multiple queries.",
        )
        parser.add_argument(
            "--query-file",
            help=(
                "Path to .txt, .json, or .jsonl queries. Text files use one query "
                "per line; JSON accepts a string list or objects with query/prompt."
            ),
        )
        parser.add_argument(
            "--ad-file",
            "--ads",
            required=True,
            help="Custom ad library JSON path.",
        )
        parser.add_argument(
            "--method",
            choices=["rag-adchat", "ad-chat", "gi-r", "gir-r", "gir-p"],
            default="rag-adchat",
            help="Injection method. Defaults to rag-adchat.",
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
            "--score-func",
            choices=["linear", "log"],
            default="linear",
            help="Ad-LLM score function. Defaults to linear.",
        )
        parser.add_argument(
            "--rag-top-k",
            type=positive_int,
            default=5,
            help="Top-k products for retrieval methods. Defaults to 5.",
        )
        parser.add_argument(
            "--topic-file",
            help="Optional Ad-Chat topic tree JSON. Generated from ad categories when omitted.",
        )
        parser.add_argument(
            "--output",
            help="Output path. Defaults to stdout.",
        )
        parser.add_argument(
            "--jsonl",
            action="store_true",
            help="Write one JSON object per line instead of a JSON array.",
        )
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Run the selected injection method and write normalized results."""
        queries = load_queries(args.query, args.query_file)
        records = load_ad_records(args.ad_file)
        product_file = None
        topic_file = None

        try:
            if args.method == "ad-chat":
                product_file = write_temp_ad_file(records, nested=True)
            else:
                product_file = write_temp_ad_file(records, nested=False)
            topic_file = args.topic_file or write_temp_topic_file(records)

            results = run_inject_method(
                method=args.method,
                queries=queries,
                product_file=product_file,
                topic_file=topic_file,
                model_name=args.model_name,
                embedding_model=args.embedding_model,
                score_func=args.score_func,
                rag_top_k=args.rag_top_k,
            )
            write_json_records(results, args.output, args.jsonl)
            return 0
        finally:
            remove_temp_file(product_file)
            if args.topic_file is None:
                remove_temp_file(topic_file)


def run_inject_method(
    method: str,
    queries: List[str],
    product_file: str,
    topic_file: str,
    model_name: str,
    embedding_model: str,
    score_func: str,
    rag_top_k: int,
) -> List[Dict[str, Any]]:
    """Run one supported injection workflow over query strings."""
    from .. import (
        AdChatWorkflow,
        AdLLMWorkflow,
        LINEAR_WEIGHT,
        LOG_WEIGHT,
        RAGAdChatWorkflow,
    )

    if method == "ad-chat":
        workflow = AdChatWorkflow(
            product_list_path=product_file,
            topic_list_path=topic_file,
            model_name=model_name,
        )
        return normalize_output_records(
            workflow.run(problem_list=queries, solution_name="chi"),
            method="ad-chat",
            queries=queries,
        )

    if method == "rag-adchat":
        workflow = RAGAdChatWorkflow(
            product_list_path=product_file,
            topic_list_path=topic_file,
            model_name=model_name,
            rag_model=embedding_model,
            top_k=rag_top_k,
        )
        return normalize_output_records(
            workflow.run(problem_list=queries),
            method="rag-adchat",
            queries=queries,
        )

    score = LINEAR_WEIGHT if score_func == "linear" else LOG_WEIGHT
    workflow = AdLLMWorkflow(
        product_list_path=product_file,
        rag_model=embedding_model,
        model_name=model_name,
        score_func=score,
    )
    method_args = {
        "gi-r": {
            "query_type": "QUERY_RESPONSE",
            "solution_name": "BASIC_GEN_INSERT",
        },
        "gir-r": {
            "query_type": "QUERY_RESPONSE",
            "solution_name": "REFINE_GEN_INSERT",
        },
        "gir-p": {
            "query_type": "QUERY_PROMPT",
            "solution_name": "REFINE_GEN_INSERT",
        },
    }
    runner = partial(workflow.run, **method_args[method])
    return normalize_output_records(
        runner(problem_list=queries),
        method=method,
        queries=queries,
    )


def load_queries(
    query_values: Optional[List[str]],
    query_file: Optional[str],
) -> List[str]:
    """Load queries from repeated CLI flags and an optional file."""
    queries = []
    if query_values:
        queries.extend(query.strip() for query in query_values if query.strip())
    if query_file:
        queries.extend(load_queries_from_file(query_file))
    if not queries:
        raise ValueError("provide at least one --query or --query-file")
    return queries


def load_queries_from_file(query_file: str) -> List[str]:
    """Load query strings from txt, JSON, or JSONL files."""
    path = Path(query_file).expanduser()
    if not path.exists():
        raise ValueError(f"query file not found: {path}")

    if path.suffix.lower() == ".jsonl":
        queries = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                queries.append(query_from_json_value(json.loads(line)))
        return queries

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [query_from_json_value(item) for item in data]
        return [query_from_json_value(data)]

    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def query_from_json_value(value: Any) -> str:
    """Extract one query string from a JSON value."""
    if isinstance(value, str):
        query = value
    elif isinstance(value, dict):
        query = value.get("query") or value.get("prompt") or value.get("question")
    else:
        query = None
    if not query or not str(query).strip():
        raise ValueError(f"invalid query record: {value}")
    return str(query).strip()


def normalize_output_records(
    records: List[Dict[str, Any]],
    method: str,
    queries: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Convert workflow outputs to the CLI result schema."""
    normalized = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            query = queries[index] if queries and index < len(queries) else None
            normalized.append(failed_output_record(method, query))
            continue
        normalized.append(
            {
                "method": method,
                "query": record.get("query"),
                "answer": record.get("answer"),
                "product": record.get("product"),
                "price": record.get("price", {"in_token": 0, "out_token": 0, "price": 0}),
            }
        )
    return normalized


def failed_output_record(method: str, query: Optional[str]) -> Dict[str, Any]:
    """Build a schema-valid record for a failed workflow call."""
    return {
        "method": method,
        "query": query,
        "answer": "QUERY_FAILED:No result generated",
        "product": {
            "name": None,
            "description": None,
            "desc": None,
            "category": None,
            "url": None,
        },
        "price": {"in_token": 0, "out_token": 0, "price": 0},
    }
