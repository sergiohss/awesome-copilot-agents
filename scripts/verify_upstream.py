#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import unicodedata
from typing import Any

from aca_tools.errors import ValidationError
from aca_tools.provenance import SourceBaseline, load_baseline, verify_lineages, verify_upstream
from aca_tools.paths import resolve_upstream_source_root


ROOT = Path(__file__).resolve().parents[1]
CSV_FIELDS = (
    "source_path",
    "source_filename_id",
    "source_declared_name",
    "canonical_id",
    "contract_id",
    "identity_disposition",
    "lineage_path",
)


def _write_json_nfc_lf(path: Path, document: dict[str, Any]) -> None:
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    lf_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(unicodedata.normalize("NFC", lf_text).encode("utf-8"))


def _pinned_blob(source_root: Path, baseline: SourceBaseline, path: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "show", f"{baseline.upstream_commit}:{path}"],
            cwd=source_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValidationError(
            f"{path}: unavailable at pinned commit {baseline.upstream_commit}"
        ) from error


def _file_record(source_root: Path, baseline: SourceBaseline, path: str) -> dict[str, Any]:
    blob = _pinned_blob(source_root, baseline, path)
    return {
        "path": path,
        "line_count": len(blob.decode("utf-8").splitlines()),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def _validate_identity_rows(
    rows: list[dict[str, str]], expected_source_paths: set[str]
) -> None:
    if len(rows) != 33 or len({row["source_path"] for row in rows}) != 33:
        raise ValidationError("agents.csv: expected 33 unique source paths")
    if {row["source_path"] for row in rows} != expected_source_paths:
        raise ValidationError("agents.csv: source paths differ from source baseline")
    if len({row["canonical_id"] for row in rows}) != 33:
        raise ValidationError("agents.csv: expected 33 unique canonical IDs")
    for index, row in enumerate(rows, start=2):
        expected_filename_id = PurePosixPath(row["source_path"]).stem
        if row["source_filename_id"] != expected_filename_id:
            raise ValidationError(
                f"agents.csv row {index} source_filename_id: "
                f"expected {expected_filename_id}, got {row['source_filename_id']!r}"
            )


def _record_baseline(source_root: Path, baseline: SourceBaseline) -> None:
    document: dict[str, Any] = {
        "schema_version": baseline.schema_version,
        "adaptation_version": baseline.adaptation_version,
        "upstream_repository": baseline.upstream_repository,
        "upstream_commit": baseline.upstream_commit,
        "agents": [
            _file_record(source_root, baseline, item.path.as_posix())
            for item in baseline.agents
        ],
        "license": {
            "path": baseline.license.path.as_posix(),
            "spdx": baseline.license.spdx,
            "sha256": hashlib.sha256(
                _pinned_blob(source_root, baseline, baseline.license.path.as_posix())
            ).hexdigest(),
            "attribution": baseline.license.attribution,
        },
        "approval": {
            "path": baseline.approval.path.as_posix(),
            "sha256": hashlib.sha256(
                _pinned_blob(source_root, baseline, baseline.approval.path.as_posix())
            ).hexdigest(),
            "ranges": [
                {"start_line": item.start_line, "end_line": item.end_line}
                for item in baseline.approval.ranges
            ],
        },
    }
    _write_json_nfc_lf(ROOT / "provenance/source-baseline.json", document)

    ledger_path = ROOT / "provenance/agents.csv"
    with ledger_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValidationError("agents.csv: unexpected columns")
        rows = list(reader)
    _validate_identity_rows(
        rows, {item.path.as_posix() for item in baseline.agents}
    )
    with ledger_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["source_path"]))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the immutable Awesome Claude Agents source authority."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Pinned awesome-claude-agents checkout (default: ACA_SOURCE_ROOT or vendor/upstream)",
    )
    parser.add_argument(
        "--distribution-root",
        type=Path,
        default=ROOT,
        help="awesome-copilot-agents root for lineage validation",
    )
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument("--record-baseline", action="store_true")
    mode.add_argument("--baseline-only", action="store_true")
    arguments = parser.parse_args()

    source_root = arguments.source_root
    if source_root is None:
        try:
            source_root = resolve_upstream_source_root(ROOT)
        except FileNotFoundError as error:
            print(f"FAIL: {error}", file=sys.stderr)
            return 1

    try:
        baseline = load_baseline(ROOT)
        if arguments.record_baseline:
            _record_baseline(source_root, baseline)
            baseline = load_baseline(ROOT)
        report = verify_upstream(source_root, baseline)
        if not arguments.baseline_only:
            lineage_issues = verify_lineages(arguments.distribution_root, baseline)
            if lineage_issues:
                print("FAIL: lineage validation failed", file=sys.stderr)
                for issue in lineage_issues:
                    print(f"- {issue}", file=sys.stderr)
                return 1
    except ValidationError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if not report.ok:
        print(
            f"FAIL: {report.matched_agents}/{report.expected_agents} current source-agent blobs; "
            f"MIT license={'match' if report.license_matches else 'mismatch'}; "
            f"root approval evidence={'match' if report.approval_matches else 'mismatch'}",
            file=sys.stderr,
        )
        for mismatch in report.mismatches:
            print(f"- {mismatch}", file=sys.stderr)
        return 1

    print(
        f"PASS: {report.matched_agents}/{report.expected_agents} current source-agent blobs, "
        "MIT license, and root approval evidence match the pinned commit"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
