from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/universal.yaml").read_text(encoding="utf-8")
)["fixtures"]

UNIVERSAL = [
    (
        "api-architect",
        ("read", "search", "edit", "execute"),
        "T-W",
        "AP-B",
        "api-design-report-v1",
        ("PROC-08",),
        ("D",),
        (),
    ),
    (
        "backend-developer",
        ("read", "search", "edit", "execute"),
        "T-W",
        "AP-B",
        "backend-implementation-v1",
        ("PROC-05", "PROC-07", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "frontend-developer",
        ("read", "search", "edit", "execute"),
        "T-W",
        "AP-B",
        "frontend-implementation-v1",
        ("PROC-05", "PROC-07", "PROC-09", "PROC-14"),
        ("H", "V"),
        (),
    ),
    (
        "tailwind-css-expert",
        ("read", "search", "edit", "execute"),
        "T-W",
        "AP-B",
        "component-delivery-v1",
        ("PROC-06", "PROC-14"),
        ("D", "V"),
        (),
    ),
]

PROFILE_SECTIONS = (
    "Role",
    "Use when",
    "Do not use when",
    "Workflow",
    "Surface behavior",
    "Result contract",
)

ALL_PROFILES_TO_DATE = {
    "tech-lead-orchestrator",
    "project-analyst",
    "team-configurator",
    "code-archaeologist",
    "code-reviewer",
    "documentation-specialist",
    "performance-optimizer",
    "api-architect",
    "backend-developer",
    "frontend-developer",
    "tailwind-css-expert",
}


@pytest.mark.parametrize("row", UNIVERSAL, ids=[row[0] for row in UNIVERSAL])
def test_universal_catalog_row_matches_spec(row):
    agent_id, tools, tool_policy, approval, contract_id, procedure_ids, surfaces, risk_gates = row
    catalog = load_catalog(PROJECT_ROOT)
    agent = next(item for item in catalog.agents if item.id == agent_id)
    assert tuple(agent.tools) == tools
    assert agent.tool_policy == tool_policy
    assert agent.approval_policy == approval
    assert agent.contract_id == contract_id
    assert agent.procedure_ids == procedure_ids
    assert agent.surfaces == surfaces
    assert agent.risk_gates == risk_gates


@pytest.mark.parametrize("agent_id", [row[0] for row in UNIVERSAL])
def test_universal_profiles_have_required_sections(agent_id: str):
    text = (PROJECT_ROOT / "src/profiles" / f"{agent_id}.md").read_text(encoding="utf-8")
    for section in PROFILE_SECTIONS:
        assert f"## {section}" in text


def test_backend_profile_states_fallback_only():
    text = (PROJECT_ROOT / "src/profiles/backend-developer.md").read_text(encoding="utf-8").lower()
    assert "fallback" in text
    assert "framework" in text


def test_frontend_profile_states_fallback_only():
    text = (PROJECT_ROOT / "src/profiles/frontend-developer.md").read_text(encoding="utf-8").lower()
    assert "fallback" in text
    assert "react" in text or "vue" in text


def test_tailwind_profile_reports_missing_visual_capability():
    text = (PROJECT_ROOT / "src/profiles/tailwind-css-expert.md").read_text(encoding="utf-8").lower()
    assert "accessibility" in text or "a11y" in text
    assert "unavailable" in text or "cannot" in text


def test_django_rest_request_prefers_django_api_developer():
    entry = next(item for item in FIXTURES if item["id"] == "django-rest-precedence")
    assert entry["expected_agent_id"] == "django-api-developer"
    assert "api-architect" in entry["excluded_alternatives"]
    assert "backend-developer" in entry["excluded_alternatives"]


def test_generic_backend_request_selects_backend_developer():
    entry = next(item for item in FIXTURES if item["id"] == "generic-backend-fallback")
    assert entry["expected_agent_id"] == "backend-developer"


def test_react_request_excludes_frontend_developer():
    entry = next(item for item in FIXTURES if item["id"] == "react-component-precedence")
    assert entry["expected_agent_id"] == "react-component-architect"
    assert "frontend-developer" in entry["excluded_alternatives"]


def test_tailwind_only_work_selects_tailwind_expert():
    entry = next(item for item in FIXTURES if item["id"] == "tailwind-utility-work")
    assert entry["expected_agent_id"] == "tailwind-css-expert"


def test_universal_handoff_fixtures_validate():
    catalog = load_catalog(PROJECT_ROOT)
    for fixture_id in (
        "api-design-report",
        "backend-implementation",
        "frontend-implementation",
        "tailwind-component-delivery",
    ):
        entry = next(item for item in FIXTURES if item["id"] == fixture_id)
        validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_eleven_profiles_are_generated():
    outputs = build_outputs(PROJECT_ROOT)
    generated = {
        path.name.removesuffix(".agent.md")
        for path in outputs
        if path.parts[:2] == (".github", "agents")
    }
    assert generated == ALL_PROFILES_TO_DATE
