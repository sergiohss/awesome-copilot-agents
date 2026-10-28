from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/core.yaml").read_text(encoding="utf-8")
)["fixtures"]

CORE = [
    (
        "code-archaeologist",
        ("read", "search", "execute"),
        "AP-R",
        "codebase-assessment-v1",
        ("PROC-01", "PROC-02", "PROC-07", "PROC-16"),
        ("H",),
        (),
    ),
    (
        "code-reviewer",
        ("read", "search", "execute"),
        "AP-R",
        "code-review-v1",
        ("PROC-12", "PROC-16"),
        ("H",),
        (),
    ),
    (
        "documentation-specialist",
        ("read", "search", "edit", "execute"),
        "AP-B",
        "documentation-changelog-v1",
        ("PROC-13",),
        ("H",),
        (),
    ),
    (
        "performance-optimizer",
        ("read", "search", "edit", "execute"),
        "AP-B",
        "performance-report-v1",
        ("PROC-11",),
        ("H",),
        ("destructive-load-test",),
    ),
]

ARCHAEOLOGIST_SECTIONS = (
    "Executive Summary",
    "Architecture Overview",
    "Module Map",
    "Data Layer",
    "API Surface",
    "Quality Signals",
    "Security Observations",
    "Performance Observations",
    "Dependencies",
    "Risks",
    "Recommended Actions",
)


@pytest.mark.parametrize("row", CORE, ids=[row[0] for row in CORE])
def test_core_catalog_row_matches_spec(row):
    agent_id, tools, approval, contract_id, procedure_ids, surfaces, risk_gates = row
    catalog = load_catalog(PROJECT_ROOT)
    agent = next(item for item in catalog.agents if item.id == agent_id)
    assert tuple(agent.tools) == tools
    assert agent.approval_policy == approval
    assert agent.contract_id == contract_id
    assert agent.procedure_ids == procedure_ids
    assert agent.surfaces == surfaces
    assert agent.risk_gates == risk_gates


def test_code_reviewer_profile_is_read_only():
    text = (PROJECT_ROOT / "src/profiles/code-reviewer.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "read-only" in lowered or "read only" in lowered
    assert "remediat" in lowered


def test_code_archaeologist_profile_lists_eleven_sections():
    text = (PROJECT_ROOT / "src/profiles/code-archaeologist.md").read_text(encoding="utf-8")
    for title in ARCHAEOLOGIST_SECTIONS:
        assert title in text


def test_django_orm_request_prefers_exact_specialist():
    entry = next(item for item in FIXTURES if item["id"] == "django-orm-precedence")
    assert entry["expected_agent_id"] == "django-orm-expert"
    assert "performance-optimizer" in entry["excluded_alternatives"]


def test_python_runtime_request_prefers_python_performance_expert():
    entry = next(item for item in FIXTURES if item["id"] == "python-runtime-precedence")
    assert entry["expected_agent_id"] == "python-performance-expert"
    assert "performance-optimizer" in entry["excluded_alternatives"]


def test_core_handoff_fixtures_validate():
    catalog = load_catalog(PROJECT_ROOT)
    for fixture_id in (
        "code-archaeologist-assessment",
        "code-reviewer-pass",
        "documentation-changelog",
        "performance-report",
    ):
        entry = next(item for item in FIXTURES if item["id"] == fixture_id)
        validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_core_profiles_are_generated():
    outputs = build_outputs(PROJECT_ROOT)
    expected = {
        "code-archaeologist",
        "code-reviewer",
        "documentation-specialist",
        "performance-optimizer",
    }
    generated = {
        path.name.removesuffix(".agent.md")
        for path in outputs
        if path.parts[:2] == (".github", "agents")
    }
    assert expected <= generated
