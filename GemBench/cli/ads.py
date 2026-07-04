import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import print_dict_rows


class AdsCommand:
    """Command group for custom ad library inspection."""

    def add_to(self, subparsers) -> None:
        """Register ad library subcommands."""
        parser = subparsers.add_parser(
            "ads",
            help="Validate and inspect custom ad libraries.",
        )
        parser.set_defaults(handler=self.handle)
        command_parsers = parser.add_subparsers(
            dest="ads_command",
            required=True,
        )
        validate_parser = command_parsers.add_parser(
            "validate",
            help="Validate a custom ad library file.",
        )
        validate_parser.add_argument(
            "ad_file",
            help="JSON ad library path.",
        )
        validate_parser.add_argument(
            "--json",
            action="store_true",
            help="Print validation summary as JSON.",
        )

    def handle(self, args) -> int:
        """Execute the selected ad library command."""
        if args.ads_command != "validate":
            raise ValueError(f"unknown ads command: {args.ads_command}")

        records = load_ad_records(args.ad_file)
        summary = ad_summary(args.ad_file, records)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            rows = [
                {"name": "file", "value": summary["file"]},
                {"name": "ads", "value": summary["count"]},
                {"name": "categories", "value": summary["category_count"]},
                {"name": "missing_url", "value": summary["missing_url"]},
            ]
            print_dict_rows(rows, ["name", "value"])
        return 0


def load_ad_records(ad_file: str) -> List[Dict[str, str]]:
    """Load a custom ad library into normalized product records."""
    path = Path(ad_file).expanduser()
    if not path.exists():
        raise ValueError(f"ad file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, dict) and "products" in data:
        data = data["products"]

    records = []
    if isinstance(data, list):
        records = [record_from_product_dict(item, None) for item in data]
    elif isinstance(data, dict) and "names" in data:
        records = records_from_flat_product_dict(data, None)
    elif isinstance(data, dict):
        for category, category_data in data.items():
            if not isinstance(category_data, dict):
                continue
            records.extend(records_from_flat_product_dict(category_data, category))
    else:
        raise ValueError("ad library must be a JSON object or list")

    records = [record for record in records if record]
    if not records:
        raise ValueError("ad library does not contain any valid ads")
    return records


def record_from_product_dict(
    product: Any,
    default_category: Optional[str],
) -> Optional[Dict[str, str]]:
    """Normalize one product-shaped dictionary into an ad record."""
    if not isinstance(product, dict):
        return None
    name = product.get("name") or product.get("title")
    description = (
        product.get("description")
        or product.get("desc")
        or product.get("text")
        or product.get("content")
    )
    if not name:
        return None
    return {
        "name": str(name),
        "description": str(description or ""),
        "category": str(product.get("category") or default_category or "General"),
        "url": str(product.get("url") or product.get("link") or ""),
    }


def records_from_flat_product_dict(
    data: Dict[str, Any],
    default_category: Optional[str],
) -> List[Dict[str, str]]:
    """Normalize a names/descriptions/urls product table into records."""
    names = data.get("names") or []
    descriptions = data.get("descriptions") or data.get("descs") or []
    urls = data.get("urls") or []
    categories = data.get("categories") or []
    records = []
    for index, name in enumerate(names):
        description = descriptions[index] if index < len(descriptions) else ""
        url = urls[index] if index < len(urls) else ""
        category = categories[index] if index < len(categories) else default_category
        records.append(
            {
                "name": str(name),
                "description": str(description or ""),
                "category": str(category or "General"),
                "url": str(url or ""),
            }
        )
    return records


def write_temp_ad_file(records: List[Dict[str, str]], nested: bool) -> str:
    """Write normalized ad records to a temporary product file."""
    data = records_to_nested_products(records) if nested else records
    return write_temp_json(data, "gembench-ads-", ".json")


def write_temp_topic_file(records: List[Dict[str, str]]) -> str:
    """Write categories from ad records to a temporary topic file."""
    return write_temp_json(records_to_topic_tree(records), "gembench-topics-", ".json")


def write_temp_json(data: Any, prefix: str, suffix: str) -> str:
    """Write JSON data to a named temporary file."""
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        prefix=prefix,
        suffix=suffix,
        delete=False,
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        return f.name


def records_to_nested_products(records: List[Dict[str, str]]) -> Dict[str, Dict[str, List[str]]]:
    """Convert normalized records to the Ad-Chat product file shape."""
    products = {}
    for record in records:
        category = record.get("category") or "General"
        if category not in products:
            products[category] = {"names": [], "urls": [], "descs": []}
        products[category]["names"].append(record["name"])
        products[category]["urls"].append(record.get("url", ""))
        products[category]["descs"].append(record.get("description", ""))
    return products


def records_to_topic_tree(records: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """Build a minimal Ad-Chat topic tree from product categories."""
    topics = {}
    for record in records:
        category = record.get("category") or "General"
        topics[category] = {}
    return topics


def ad_summary(ad_file: str, records: List[Dict[str, str]]) -> Dict[str, Any]:
    """Build validation summary data for an ad library."""
    categories = sorted({record.get("category") or "General" for record in records})
    return {
        "file": str(Path(ad_file).expanduser()),
        "count": len(records),
        "category_count": len(categories),
        "categories": categories,
        "missing_url": sum(1 for record in records if not record.get("url")),
    }


def remove_temp_file(file_path: Optional[str]) -> None:
    """Remove a temporary file when it exists."""
    if not file_path:
        return
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass
