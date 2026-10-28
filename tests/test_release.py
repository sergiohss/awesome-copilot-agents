from __future__ import annotations

from pathlib import Path

from aca_tools.paths import resolve_upstream_source_root
from aca_tools.release import validate_release


PROJECT_ROOT = Path(__file__).parents[1]
SOURCE_ROOT = resolve_upstream_source_root(PROJECT_ROOT)


def test_development_dimensions_include_catalog_and_provenance():
    report = validate_release(PROJECT_ROOT, source_root=SOURCE_ROOT)
    names = {item.name for item in report.dimensions}
    assert {"identity", "procedures", "generation", "upstream", "provenance", "surface_smoke"} <= names
    identity = next(item for item in report.dimensions if item.name == "identity")
    assert identity.complete


def test_release_requires_smoke_evidence():
    report = validate_release(PROJECT_ROOT, source_root=SOURCE_ROOT)
    smoke = next(item for item in report.dimensions if item.name == "surface_smoke")
    assert smoke.complete
    assert report.release_eligible
