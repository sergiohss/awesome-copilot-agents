#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from aca_tools.cli import main as generate_main
from aca_tools.errors import ValidationError
from aca_tools.install import apply_install, apply_uninstall, plan_install, plan_uninstall


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or uninstall Copilot packages.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "upgrade", "uninstall"):
        cmd = sub.add_parser(name)
        cmd.add_argument("package_kind", choices=["repository"])
        cmd.add_argument("--target", type=Path, required=True)
    arguments = parser.parse_args()
    manifest = ROOT / "packages/manifests/repository.json"
    portable = ROOT / "packages/repository/portable"
    target = arguments.target
    state = target / ".github/.awesome-copilot-agents-install.json"
    try:
        if arguments.command == "uninstall":
            plan = plan_uninstall(state, target)
            apply_uninstall(plan)
            return 0
        plan = plan_install(ROOT, target)
        if plan.conflicts:
            raise ValidationError("install conflicts detected")
        apply_install(
            plan,
            package_root=portable,
            target_root=target,
            manifest_path=manifest,
        )
    except ValidationError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
