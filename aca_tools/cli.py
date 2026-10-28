from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .errors import ValidationError
from .generate import generate


def main(argv: Sequence[str] | None = None, *, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Copilot packages.")
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    parser.add_argument(
        "--release",
        action="store_true",
        help="require the complete 33-agent and 21-skill catalog",
    )
    parser.add_argument("--root", type=Path, default=root or Path.cwd(), help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)

    try:
        report = generate(
            arguments.root.resolve(),
            check=arguments.check,
            require_complete=arguments.release,
        )
    except ValidationError as error:
        print(f"generation failed: {error}", file=sys.stderr)
        return 2

    print(
        f"generated {len(report.written_paths)} files; "
        f"changed paths: {len(report.changed_paths)}; "
        f"complete: {str(report.complete).lower()}"
    )
    return 1 if arguments.check and report.changed_paths else 0
