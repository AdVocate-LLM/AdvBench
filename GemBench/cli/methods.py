import json
from typing import Any, Dict, List

from .common import print_dict_rows
from .constants import METHODS


def method_rows() -> List[Dict[str, str]]:
    """Build printable rows for supported injection methods."""
    return [
        {
            "key": key,
            "name": value["name"],
            "tasks": ",".join(value["tasks"]),
            "description": value["description"],
        }
        for key, value in METHODS.items()
    ]


class MethodsCommand:
    """Command group for production injection method discovery."""

    def add_to(self, subparsers: Any) -> None:
        """Register method discovery subcommands."""
        parser = subparsers.add_parser(
            "methods",
            help="Inspect production injection methods.",
        )
        parser.set_defaults(handler=self.handle)
        command_parsers = parser.add_subparsers(
            dest="methods_command",
            required=True,
        )
        list_parser = command_parsers.add_parser(
            "list",
            help="List built-in injection methods.",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="Print methods as JSON.",
        )

    def handle(self, args) -> int:
        """Execute the selected methods command."""
        if args.methods_command != "list":
            raise ValueError(f"unknown methods command: {args.methods_command}")

        rows = method_rows()
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print_dict_rows(rows, ["key", "name", "tasks", "description"])
        return 0


class BaselinesCommand:
    """Command group for benchmark baseline discovery."""

    def add_to(self, subparsers: Any) -> None:
        """Register baseline discovery subcommands."""
        parser = subparsers.add_parser(
            "baselines",
            help="Inspect built-in baseline methods.",
        )
        parser.set_defaults(handler=self.handle)
        command_parsers = parser.add_subparsers(
            dest="baselines_command",
            required=True,
        )
        list_parser = command_parsers.add_parser(
            "list",
            help="List built-in baseline methods.",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="Print baselines as JSON.",
        )

    def handle(self, args) -> int:
        """Execute the selected baselines command."""
        if args.baselines_command != "list":
            raise ValueError(f"unknown baselines command: {args.baselines_command}")

        rows = method_rows()
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            print_dict_rows(rows, ["key", "name", "tasks", "description"])
        return 0
