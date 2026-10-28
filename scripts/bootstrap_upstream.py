#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from aca_tools.errors import ValidationError
from aca_tools.paths import is_upstream_source_root, upstream_vendor_dir
from aca_tools.provenance import load_baseline


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clone or update the pinned awesome-claude-agents upstream checkout."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args()

    try:
        baseline = load_baseline(arguments.root)
    except ValidationError as error:
        print(error, file=sys.stderr)
        return 1

    destination = upstream_vendor_dir(arguments.root)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        subprocess.run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                baseline.upstream_repository,
                str(destination),
            ],
            check=True,
        )
    subprocess.run(
        ["git", "-C", str(destination), "fetch", "origin", baseline.upstream_commit],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(destination), "checkout", "--detach", baseline.upstream_commit],
        check=True,
    )

    if not is_upstream_source_root(destination):
        print(
            f"Checkout at {destination} is missing expected agent files after "
            f"{baseline.upstream_commit}.",
            file=sys.stderr,
        )
        return 1

    print(f"Upstream ready at {destination} ({baseline.upstream_commit})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
