from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .errors import ValidationError
from .generate import generate
from .loaders import load_catalog
from .provenance import load_baseline, verify_lineages, verify_upstream


@dataclass(frozen=True, slots=True)
class CoverageDimension:
    name: str
    complete: bool
    detail: str


@dataclass(frozen=True, slots=True)
class CoverageReport:
    dimensions: tuple[CoverageDimension, ...]
    release_eligible: bool

    @property
    def complete(self) -> bool:
        return self.release_eligible and all(item.complete for item in self.dimensions)


def validate_release(root: Path, *, source_root: Path) -> CoverageReport:
    root = root.resolve()
    catalog = load_catalog(root)
    baseline = load_baseline(root)
    dimensions: list[CoverageDimension] = []

    dimensions.append(
        CoverageDimension(
            "identity",
            len(catalog.agents) == 33,
            f"{len(catalog.agents)}/33 agents",
        )
    )
    dimensions.append(
        CoverageDimension(
            "procedures",
            len(catalog.procedures) == 21,
            f"{len(catalog.procedures)}/21 procedures",
        )
    )

    report = generate(root, check=True, require_complete=True)
    dimensions.append(
        CoverageDimension(
            "generation",
            report.complete and not report.changed_paths,
            f"complete={report.complete} drift={len(report.changed_paths)}",
        )
    )

    upstream = verify_upstream(source_root, baseline)
    dimensions.append(
        CoverageDimension(
            "upstream",
            upstream.ok,
            f"{upstream.matched_agents}/{upstream.expected_agents} blobs",
        )
    )

    lineage_issues = verify_lineages(root, baseline)
    dimensions.append(
        CoverageDimension(
            "provenance",
            not lineage_issues,
            "ok" if not lineage_issues else lineage_issues[0],
        )
    )

    evidence_dir = root / "smoke/evidence"
    evidence_files = sorted(evidence_dir.glob("*.json")) if evidence_dir.is_dir() else []
    required_surfaces = {"vscode", "cli", "cloud", "installation"}
    seen = {
        json.loads(path.read_text(encoding="utf-8")).get("surface")
        for path in evidence_files
    }
    smoke_complete = required_surfaces.issubset(seen) and all(
        json.loads(path.read_text(encoding="utf-8")).get("observed_status") == "passed"
        for path in evidence_files
    )
    dimensions.append(
        CoverageDimension(
            "surface_smoke",
            smoke_complete,
            f"{len(evidence_files)} evidence files",
        )
    )

    release_eligible = all(item.complete for item in dimensions)
    return CoverageReport(dimensions=tuple(dimensions), release_eligible=release_eligible)


def ensure_release_ready(root: Path, *, source_root: Path) -> CoverageReport:
    report = validate_release(root, source_root=source_root)
    if not report.release_eligible:
        failing = [item for item in report.dimensions if not item.complete]
        raise ValidationError(
            "release validation failed: "
            + "; ".join(f"{item.name} ({item.detail})" for item in failing)
        )
    return report
