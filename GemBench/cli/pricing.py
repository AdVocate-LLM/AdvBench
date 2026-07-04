import json
from typing import Any

from ..benchmarking.tools.ModelPrice import ModelPricing
from .common import add_price_file_arg, non_negative_float, print_price_table


class PricingCommand:
    """Command group for pricing table inspection and overrides."""

    def add_to(self, subparsers: Any) -> None:
        """Register pricing subcommands."""
        parser = subparsers.add_parser(
            "pricing",
            help="Inspect and customize model pricing.",
        )
        parser.set_defaults(handler=self.handle)
        command_parsers = parser.add_subparsers(
            dest="pricing_command",
            required=True,
        )

        list_parser = command_parsers.add_parser(
            "list",
            help="List model prices.",
        )
        add_price_file_arg(list_parser)
        list_parser.add_argument(
            "--custom-only",
            action="store_true",
            help="Only list models from the custom price file.",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="Print the price table as JSON.",
        )

        get_parser = command_parsers.add_parser(
            "get",
            help="Show one model price.",
        )
        add_price_file_arg(get_parser)
        get_parser.add_argument("model")
        get_parser.add_argument(
            "--json",
            action="store_true",
            help="Print the model price as JSON.",
        )

        add_parser = command_parsers.add_parser(
            "add",
            aliases=["set"],
            help="Add or replace one custom model price.",
        )
        add_price_file_arg(add_parser)
        add_parser.add_argument("model")
        add_parser.add_argument(
            "--input-price",
            type=non_negative_float,
            required=True,
            help="Input price for the selected unit.",
        )
        add_parser.add_argument(
            "--output-price",
            type=non_negative_float,
            default=0,
            help="Output price for the selected unit. Defaults to 0.",
        )
        add_parser.add_argument(
            "--request-price",
            type=non_negative_float,
            default=0,
            help="Fixed request price. Defaults to 0.",
        )
        add_parser.add_argument(
            "--unit",
            choices=["per-m", "per-1k"],
            default="per-m",
            help="Unit for input/output prices. Defaults to per-m.",
        )

        remove_parser = command_parsers.add_parser(
            "remove",
            aliases=["rm"],
            help="Remove one model from the custom price file.",
        )
        add_price_file_arg(remove_parser)
        remove_parser.add_argument("model")

        path_parser = command_parsers.add_parser(
            "path",
            help="Print the custom price file path.",
        )
        add_price_file_arg(path_parser)

    def handle(self, args) -> int:
        """Dispatch to the selected pricing subcommand."""
        if args.pricing_command == "list":
            return self.list(args)
        if args.pricing_command == "get":
            return self.get(args)
        if args.pricing_command in {"add", "set"}:
            return self.add(args)
        if args.pricing_command in {"remove", "rm"}:
            return self.remove(args)
        if args.pricing_command == "path":
            pricing = ModelPricing(include_custom_prices=False)
            print(pricing._price_file_path(args.price_file))
            return 0
        raise ValueError(f"unknown pricing command: {args.pricing_command}")

    def list(self, args) -> int:
        """Print the merged or custom-only model price table."""
        pricing = ModelPricing(price_file=args.price_file, include_custom_prices=False)
        prices = (
            pricing.load_custom_prices(args.price_file)
            if args.custom_only
            else pricing.load_price_table(args.price_file)
        )
        if args.json:
            print(json.dumps(prices, indent=2, sort_keys=True))
        else:
            print_price_table(prices)
        return 0

    def get(self, args) -> int:
        """Print one model price entry."""
        pricing = ModelPricing(price_file=args.price_file, include_custom_prices=False)
        prices = pricing.load_price_table(args.price_file)
        if args.model not in prices:
            raise ValueError(f"{args.model} not found in price table")
        price = prices[args.model]
        if args.json:
            print(json.dumps({args.model: price}, indent=2))
        else:
            print_price_table({args.model: price})
        return 0

    def add(self, args) -> int:
        """Add or replace one custom model price."""
        pricing = ModelPricing(price_file=args.price_file, include_custom_prices=False)
        input_price = args.input_price
        output_price = args.output_price
        if args.unit == "per-1k":
            input_price *= 1000
            output_price *= 1000

        path = pricing.set_custom_price(
            args.model,
            input_price,
            output_price,
            args.request_price,
            args.price_file,
        )
        print(f"saved {args.model} to {path}")
        return 0

    def remove(self, args) -> int:
        """Remove one model from the custom price file."""
        pricing = ModelPricing(price_file=args.price_file, include_custom_prices=False)
        removed = pricing.remove_custom_price(args.model, args.price_file)
        if removed:
            print(f"removed custom price for {args.model}")
            return 0
        print(f"no custom price found for {args.model}")
        return 1
