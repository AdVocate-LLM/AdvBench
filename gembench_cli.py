"""
Console launcher for the GEM-Bench CLI.
"""
import sys
from pathlib import Path


def _ensure_distribution_root_first():
    """Prefer this installed distribution when another editable package also has GemBench."""
    distribution_root = str(Path(__file__).resolve().parent)
    try:
        sys.path.remove(distribution_root)
    except ValueError:
        pass
    sys.path.insert(0, distribution_root)


def main():
    """Run the GEM-Bench command line interface."""
    _ensure_distribution_root_first()
    from GemBench.cli import main as run_cli

    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
