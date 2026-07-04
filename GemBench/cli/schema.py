import json
from typing import Any, Dict

from .common import print_dict_rows


SCHEMAS: Dict[str, Dict[str, Any]] = {
    "ad-library": {
        "description": "Custom product ads used by gembench inject.",
        "required": ["name"],
        "optional": ["description", "desc", "category", "url", "link"],
        "examples": [
            {
                "name": "ThermoCoat Parka",
                "description": "Insulated winter parka",
                "category": "travel",
                "url": "https://example.com/thermocoat",
            }
        ],
        "accepted_shapes": [
            "list of product objects",
            "flat product dictionary with names/descriptions/urls arrays",
            "category-keyed product dictionaries",
        ],
    },
    "query-record": {
        "description": "One external query record for --query-file JSONL input.",
        "required_any": ["query", "prompt", "question"],
        "examples": [
            {"query": "What should I pack for a winter trip to Korea?"},
            {"prompt": "How do I fit winter clothes into a carry-on?"},
        ],
    },
    "inject-result": {
        "description": "One record emitted by gembench inject.",
        "required": ["method", "query", "answer", "product", "price"],
        "price": {
            "required": ["in_token", "out_token", "price"],
        },
        "examples": [
            {
                "method": "rag-adchat",
                "query": "What should I pack for a winter trip to Korea?",
                "answer": "Pack warm layers and consider ThermoCoat Parka.",
                "product": {
                    "name": "ThermoCoat Parka",
                    "description": "Insulated winter parka",
                    "category": "travel",
                    "url": "https://example.com/thermocoat",
                },
                "price": {
                    "in_token": 12,
                    "out_token": 9,
                    "price": 0.00042,
                },
            }
        ],
    },
    "score-output": {
        "description": "Production JSON emitted by gembench score --json or --output.",
        "required": ["summary", "scores"],
        "summary_row": ["method", "matrix", "count", "average", "min", "max"],
        "score_row": [
            "method",
            "dataset",
            "repeat_id",
            "matrix",
            "category",
            "query",
            "answer",
            "product",
            "score",
        ],
    },
}


class SchemaCommand:
    """Command for inspecting production CLI data schemas."""

    def add_to(self, subparsers: Any) -> None:
        """Register schema inspection subcommands."""
        parser = subparsers.add_parser(
            "schema",
            aliases=["schemas"],
            help="Inspect supported production input and output schemas.",
        )
        parser.set_defaults(handler=self.handle)
        command_parsers = parser.add_subparsers(
            dest="schema_command",
            required=True,
        )
        list_parser = command_parsers.add_parser(
            "list",
            help="List available schemas.",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="Print schemas as JSON.",
        )

        show_parser = command_parsers.add_parser(
            "show",
            help="Show one schema.",
        )
        show_parser.add_argument(
            "name",
            choices=sorted(SCHEMAS.keys()),
        )
        show_parser.add_argument(
            "--json",
            action="store_true",
            help="Print schema as JSON.",
        )

    def handle(self, args) -> int:
        """Execute the selected schema command."""
        if args.schema_command == "list":
            return self.list(args)
        if args.schema_command == "show":
            return self.show(args)
        raise ValueError(f"unknown schema command: {args.schema_command}")

    def list(self, args) -> int:
        """Print available schema names."""
        rows = [
            {
                "name": name,
                "description": schema["description"],
            }
            for name, schema in sorted(SCHEMAS.items())
        ]
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print_dict_rows(rows, ["name", "description"])
        return 0

    def show(self, args) -> int:
        """Print one schema definition."""
        schema = SCHEMAS[args.name]
        if args.json:
            print(json.dumps({args.name: schema}, indent=2))
        else:
            print(json.dumps({args.name: schema}, indent=2))
        return 0
