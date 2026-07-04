import argparse
import sys
from typing import Iterable, Optional

from .ads import AdsCommand
from .analysis import CompareCommand, ReportCommand
from .benchmark import (
    DatasetsCommand,
    DiagnoseCommand,
    EvaluateCommand,
    GenerateCommand,
    RunCommand,
)
from .common import load_dotenv
from .inject import InjectCommand
from .methods import BaselinesCommand, MethodsCommand
from .pricing import PricingCommand
from .score import ScoreCommand
from .schema import SchemaCommand


class CliApp:
    """Top-level command dispatcher for the gembench CLI."""

    def __init__(self) -> None:
        """Register command handlers in CLI display order."""
        self.commands = [
            InjectCommand(),
            ScoreCommand(),
            ReportCommand(),
            CompareCommand(),
            AdsCommand(),
            SchemaCommand(),
            MethodsCommand(),
            PricingCommand(),
            DatasetsCommand(),
            BaselinesCommand(),
            GenerateCommand(),
            RunCommand(),
            EvaluateCommand(),
            DiagnoseCommand(),
        ]

    def build_parser(self) -> argparse.ArgumentParser:
        """Build the root argument parser and attach subcommands."""
        parser = argparse.ArgumentParser(
            prog="gembench",
            description="GemBench command line tools.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)
        for command in self.commands:
            command.add_to(subparsers)
        return parser

    def run(self, argv: Optional[Iterable[str]] = None) -> int:
        """Parse CLI arguments and execute the selected command."""
        load_dotenv()
        parser = self.build_parser()
        args = parser.parse_args(list(argv) if argv is not None else None)
        try:
            return args.handler(args)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Run the gembench CLI entry point."""
    return CliApp().run(argv)
