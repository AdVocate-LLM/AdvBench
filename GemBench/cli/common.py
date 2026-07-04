import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_dotenv() -> None:
    """Load .env when python-dotenv is available."""
    try:
        from dotenv import load_dotenv as _load_dotenv
    except ImportError:
        return
    _load_dotenv()


def add_price_file_arg(parser: argparse.ArgumentParser) -> None:
    """Add the shared custom pricing table argument."""
    parser.add_argument(
        "--price-file",
        help=(
            "Custom price JSON path. Defaults to GEMBENCH_MODEL_PRICE_FILE "
            "or ~/.gembench/model_prices.json."
        ),
    )


def add_matrix_args(parser: argparse.ArgumentParser, matrixes: List[str]) -> None:
    """Add repeated evaluation matrix arguments."""
    parser.add_argument(
        "--matrix",
        action="append",
        help=(
            "Evaluation matrix to run. Repeat or comma-separate values. "
            f"Known values: {', '.join(matrixes)}."
        ),
    )


def print_price_table(prices: Dict[str, Any]) -> None:
    """Print model prices as an aligned text table."""
    rows = [
        (model, value[0], value[1], value[2])
        for model, value in sorted(prices.items())
    ]
    headers = ("model", "input/M", "output/M", "request")
    widths = [
        max(len(str(row[index])) for row in rows + [headers])
        for index in range(len(headers))
    ]
    print(
        "  ".join(
            header.ljust(widths[index])
            for index, header in enumerate(headers)
        )
    )
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(
            "  ".join(
                str(value).ljust(widths[index])
                for index, value in enumerate(row)
            )
        )


def print_dict_rows(rows: List[Dict[str, Any]], headers: List[str]) -> None:
    """Print dictionaries as an aligned text table."""
    widths = [
        max(len(str(row.get(header, ""))) for row in rows + [{header: header}])
        for header in headers
    ]
    print(
        "  ".join(
            header.ljust(widths[index])
            for index, header in enumerate(headers)
        )
    )
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(
            "  ".join(
                str(row.get(header, "")).ljust(widths[index])
                for index, header in enumerate(headers)
            )
        )


def write_json_records(
    records: List[Dict[str, Any]],
    output: Optional[str],
    jsonl: bool,
) -> None:
    """Write records as JSON or JSONL to stdout or a file."""
    if jsonl:
        content = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        if content:
            content += "\n"
    else:
        content = json.dumps(records, indent=2, ensure_ascii=False) + "\n"

    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        print(content, end="")


def add_check(
    checks: List[Dict[str, str]],
    name: str,
    status: str,
    detail: str,
) -> None:
    """Append one diagnostic check row."""
    checks.append({"name": name, "status": status, "detail": detail})


def add_env_check(
    checks: List[Dict[str, str]],
    name: str,
    fallback: Optional[str] = None,
) -> None:
    """Append a diagnostic row for an environment variable."""
    if os.environ.get(name):
        add_check(checks, f"env:{name}", "ok", "configured")
        return
    if fallback and os.environ.get(fallback):
        add_check(
            checks,
            f"env:{name}",
            "warning",
            f"not set; will fall back to {fallback}",
        )
        return
    add_check(checks, f"env:{name}", "warning", "not set")


def non_negative_float(value: str) -> float:
    """Parse an argparse float that must be zero or positive."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("price must be non-negative")
    return parsed


def non_negative_int(value: str) -> int:
    """Parse an argparse integer that must be zero or positive."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def positive_int(value: str) -> int:
    """Parse an argparse integer that must be greater than zero."""
    parsed = non_negative_int(value)
    if parsed == 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed
