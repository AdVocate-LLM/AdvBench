import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import print_dict_rows


class ReportCommand:
    """Command for summarizing production score outputs."""

    def add_to(self, subparsers: Any) -> None:
        """Register report command arguments."""
        parser = subparsers.add_parser(
            "report",
            help="Summarize or export gembench score outputs.",
        )
        parser.add_argument(
            "scores",
            nargs="+",
            help="Score JSON or JSONL files produced by gembench score.",
        )
        parser.add_argument(
            "--method",
            action="append",
            help="Method to include. Repeat or comma-separate values.",
        )
        parser.add_argument(
            "--matrix",
            action="append",
            help="Matrix to include. Repeat or comma-separate values.",
        )
        parser.add_argument(
            "--detail",
            action="store_true",
            help="Show per-record score rows instead of summary rows.",
        )
        parser.add_argument(
            "--format",
            choices=["table", "json", "csv"],
            default="table",
            help="Output format. Defaults to table.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Shortcut for --format json.",
        )
        parser.add_argument(
            "--output",
            help="Write report output to this path.",
        )
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Load score files and write a summary or detail report."""
        rows = load_score_rows_from_files(args.scores)
        rows = filter_score_rows(rows, args.method, args.matrix)
        payload = {
            "summary": summarize_score_rows(rows),
            "scores": rows,
        }
        output_rows = payload["scores"] if args.detail else payload["summary"]
        output_format = "json" if args.json else args.format
        write_rows_output(output_rows, payload, output_format, args.output)
        return 0


class CompareCommand:
    """Command for comparing scored GEM-Bench methods."""

    def add_to(self, subparsers: Any) -> None:
        """Register compare command arguments."""
        parser = subparsers.add_parser(
            "compare",
            help="Compare methods across one or more score outputs.",
        )
        parser.add_argument(
            "scores",
            nargs="+",
            help="Score JSON or JSONL files produced by gembench score.",
        )
        parser.add_argument(
            "--baseline",
            help="Method name to use as the delta baseline.",
        )
        parser.add_argument(
            "--method",
            action="append",
            help="Method to include. Repeat or comma-separate values.",
        )
        parser.add_argument(
            "--matrix",
            action="append",
            help="Matrix to include. Repeat or comma-separate values.",
        )
        parser.add_argument(
            "--format",
            choices=["table", "json", "csv"],
            default="table",
            help="Output format. Defaults to table.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Shortcut for --format json.",
        )
        parser.add_argument(
            "--output",
            help="Write compare output to this path.",
        )
        parser.set_defaults(handler=self.handle)

    def handle(self, args) -> int:
        """Load score files and compare method averages."""
        rows = load_score_rows_from_files(args.scores)
        rows = filter_score_rows(rows, args.method, args.matrix)
        payload = build_compare_payload(rows, args.baseline)
        output_format = "json" if args.json else args.format
        write_rows_output(payload["comparison"], payload, output_format, args.output)
        return 0


def load_score_rows_from_files(paths: List[str]) -> List[Dict[str, Any]]:
    """Load and annotate score rows from one or more files."""
    rows = []
    for path_value in paths:
        path = Path(path_value).expanduser()
        for row in load_score_rows(path):
            row = dict(row)
            row.setdefault("source", str(path))
            rows.append(row)
    if not rows:
        raise ValueError("no score rows found")
    return rows


def load_score_rows(path: Path) -> List[Dict[str, Any]]:
    """Load score rows from score JSON, score JSONL, or a row list."""
    if not path.exists():
        raise ValueError(f"score file not found: {path}")

    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return validate_score_rows(rows, path)

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "scores" in data:
        rows = data["scores"]
    elif isinstance(data, dict):
        rows = [data]
    else:
        rows = data
    return validate_score_rows(rows, path)


def validate_score_rows(rows: Any, path: Path) -> List[Dict[str, Any]]:
    """Validate that score data is a list of score-row objects."""
    if not isinstance(rows, list):
        raise ValueError(f"score data must be a list or object: {path}")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"score row {index} must be an object: {path}")
        for field in ["method", "matrix", "score"]:
            if field not in row:
                raise ValueError(f"score row {index} missing {field}: {path}")
    return rows


def filter_score_rows(
    rows: List[Dict[str, Any]],
    methods: Optional[List[str]],
    matrixes: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """Filter score rows by method and matrix values."""
    method_set = set(parse_repeated_values(methods))
    matrix_set = set(parse_repeated_values(matrixes))
    filtered = []
    for row in rows:
        if method_set and row.get("method") not in method_set:
            continue
        if matrix_set and row.get("matrix") not in matrix_set:
            continue
        filtered.append(row)
    if not filtered:
        raise ValueError("no score rows match the selected filters")
    return filtered


def parse_repeated_values(values: Optional[List[str]]) -> List[str]:
    """Parse repeated or comma-separated CLI values."""
    parsed = []
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item and item not in parsed:
                parsed.append(item)
    return parsed


def summarize_score_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate score rows by method and matrix."""
    grouped: Dict[tuple, List[float]] = {}
    for row in rows:
        key = (str(row.get("method", "")), str(row.get("matrix", "")))
        grouped.setdefault(key, []).append(float(row.get("score", 0)))

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


def build_compare_payload(
    rows: List[Dict[str, Any]],
    baseline: Optional[str],
) -> Dict[str, Any]:
    """Build method comparison rows from score rows."""
    summary = summarize_score_rows(rows)
    if baseline and not any(row["method"] == baseline for row in summary):
        raise ValueError(f"baseline method not found in score rows: {baseline}")
    baseline_scores = {
        row["matrix"]: row["average"]
        for row in summary
        if baseline and row["method"] == baseline
    }
    comparison = []
    for row in summary:
        delta = None
        if baseline and row["matrix"] in baseline_scores:
            delta = row["average"] - baseline_scores[row["matrix"]]
        comparison.append(
            {
                "method": row["method"],
                "matrix": row["matrix"],
                "count": row["count"],
                "average": row["average"],
                "delta_vs_baseline": delta,
                "min": row["min"],
                "max": row["max"],
            }
        )
    return {
        "baseline": baseline,
        "comparison": comparison,
        "scores": rows,
    }


def write_rows_output(
    rows: List[Dict[str, Any]],
    payload: Dict[str, Any],
    output_format: str,
    output: Optional[str],
) -> None:
    """Write rows or payload in table, JSON, or CSV format."""
    if output_format == "json":
        content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        write_text(content, output)
        return
    if output_format == "csv":
        write_csv_rows(rows, output)
        return
    if output:
        write_text(format_table(rows), output)
    else:
        print_dict_rows(format_rows_for_table(rows), table_headers(rows))


def write_csv_rows(rows: List[Dict[str, Any]], output: Optional[str]) -> None:
    """Write row dictionaries as CSV."""
    headers = table_headers(rows)
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(format_rows_for_csv(rows, headers))
        return

    writer = csv.DictWriter(sys.stdout, fieldnames=headers)
    writer.writeheader()
    writer.writerows(format_rows_for_csv(rows, headers))


def write_text(content: str, output: Optional[str]) -> None:
    """Write text to stdout or a file."""
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


def table_headers(rows: List[Dict[str, Any]]) -> List[str]:
    """Choose stable table headers for report rows."""
    preferred = [
        "source",
        "method",
        "matrix",
        "count",
        "average",
        "delta_vs_baseline",
        "min",
        "max",
        "category",
        "query",
        "score",
    ]
    keys = []
    for key in preferred:
        if any(key in row for row in rows):
            keys.append(key)
    for row in rows:
        for key in row:
            if key not in keys and key not in {"answer", "product", "dataset", "repeat_id"}:
                keys.append(key)
    return keys


def format_rows_for_table(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format row values for compact text tables."""
    return [format_row(row, truncate=True) for row in rows]


def format_rows_for_csv(
    rows: List[Dict[str, Any]],
    headers: List[str],
) -> List[Dict[str, Any]]:
    """Format row values for CSV output."""
    formatted = []
    for row in rows:
        value = format_row(row, truncate=False)
        formatted.append({header: value.get(header, "") for header in headers})
    return formatted


def format_row(row: Dict[str, Any], truncate: bool) -> Dict[str, Any]:
    """Format nested and numeric row values."""
    formatted = {}
    for key, value in row.items():
        if isinstance(value, float):
            formatted[key] = f"{value:.6g}"
        elif value is None:
            formatted[key] = ""
        elif isinstance(value, (dict, list)):
            formatted[key] = json.dumps(value, ensure_ascii=False)
        else:
            text = str(value)
            if truncate and key in {"query", "answer"} and len(text) > 80:
                text = text[:77] + "..."
            formatted[key] = text
    return formatted


def format_table(rows: List[Dict[str, Any]]) -> str:
    """Render rows to the same simple table format used by print_dict_rows."""
    headers = table_headers(rows)
    table_rows = format_rows_for_table(rows)
    widths = [
        max(len(str(row.get(header, ""))) for row in table_rows + [{header: header}])
        for header in headers
    ]
    lines = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)),
        "  ".join("-" * width for width in widths),
    ]
    for row in table_rows:
        lines.append(
            "  ".join(
                str(row.get(header, "")).ljust(widths[index])
                for index, header in enumerate(headers)
            )
        )
    return "\n".join(lines) + "\n"
