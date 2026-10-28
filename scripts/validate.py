#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from aca_tools.errors import ValidationError
from aca_tools.release import validate_release


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/var/www/projetos/awesome-claude-agents")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate awesome-copilot-agents release readiness.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--development", action="store_true")
    mode.add_argument("--release", action="store_true")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args()

    try:
        report = validate_release(arguments.root, source_root=arguments.source_root)
    except ValidationError as error:
        print(json.dumps({"ok": False, "error": str(error)}), indent=2)
        return 1

    payload = {
        "ok": report.complete if arguments.release else True,
        "release_eligible": report.release_eligible,
        "dimensions": [
            {"name": item.name, "complete": item.complete, "detail": item.detail}
            for item in report.dimensions
        ],
    }
    if arguments.release and not report.release_eligible:
        payload["ok"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
