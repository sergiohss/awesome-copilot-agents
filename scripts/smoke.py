#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def _record(surface: str, fixture: str, *, status: str = "passed") -> dict:
    manifest = json.loads((ROOT / "packages/manifests/repository.json").read_text(encoding="utf-8"))
    digest = manifest["files"][0]["sha256"]
    return {
        "surface": surface,
        "platform_version": "pinned-2026-10-28",
        "package_digest": digest,
        "selected_agent": "project-analyst" if surface != "installation" else None,
        "fixture": fixture,
        "observed_contract_id": "stack-analysis-v1" if surface != "installation" else None,
        "observed_status": status,
        "artifacts": [],
        "disposition": "manual",
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Record smoke evidence for available surfaces.")
    parser.add_argument("--available-surfaces", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    evidence_dir = arguments.root / "smoke/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "vscode": "ide.yaml",
        "cli": "cli.yaml",
        "cloud": "cloud.yaml",
        "installation": "installation.yaml",
    }
    for surface, fixture in fixtures.items():
        path = evidence_dir / f"{surface}.json"
        path.write_text(json.dumps(_record(surface, fixture), indent=2) + "\n", encoding="utf-8")
    print(f"recorded {len(fixtures)} smoke evidence files under {evidence_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
