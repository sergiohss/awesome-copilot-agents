from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/backend-frameworks.yaml").read_text(encoding="utf-8")
)["fixtures"]

BACKEND_FRAMEWORK = [
    (
        "laravel-backend-expert",
        "laravel-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "laravel-eloquent-expert",
        "eloquent-work-summary-v1",
        ("PROC-06", "PROC-07", "PROC-09", "PROC-10"),
        ("D",),
        ("destructive-migration",),
    ),
    (
        "django-backend-expert",
        "django-backend-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "django-api-developer",
        "django-api-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-08", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "django-orm-expert",
        "django-orm-optimization-v1",
        ("PROC-06", "PROC-07", "PROC-10", "PROC-11"),
        ("H", "D"),
        ("destructive-migration",),
    ),
    (
        "rails-backend-expert",
        "rails-backend-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "rails-api-developer",
        "rails-api-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-08", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "rails-activerecord-expert",
        "rails-activerecord-optimization-v1",
        ("PROC-06", "PROC-07", "PROC-10", "PROC-11"),
        ("H", "D"),
        ("destructive-migration",),
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

EXPECTED_PROFILE_COUNT = 19


@pytest.mark.parametrize("row", BACKEND_FRAMEWORK, ids=[row[0] for row in BACKEND_FRAMEWORK])
def test_backend_framework_catalog_row_matches_spec(row):
    agent_id, contract_id, procedure_ids, surfaces, risk_gates = row
    catalog = load_catalog(PROJECT_ROOT)
    agent = next(item for item in catalog.agents if item.id == agent_id)
    assert agent.tool_policy == "T-W"
    assert agent.approval_policy == "AP-B"
    assert tuple(agent.tools) == ("read", "search", "edit", "execute")
    assert agent.contract_id == contract_id
    assert agent.procedure_ids == procedure_ids
    assert agent.surfaces == surfaces
    assert agent.risk_gates == risk_gates


@pytest.mark.parametrize("agent_id", [row[0] for row in BACKEND_FRAMEWORK])
def test_backend_framework_profiles_have_required_sections(agent_id: str):
    text = (PROJECT_ROOT / "src/profiles" / f"{agent_id}.md").read_text(encoding="utf-8")
    for section in PROFILE_SECTIONS:
        assert f"## {section}" in text


def test_laravel_application_logic_selects_backend_expert():
    entry = next(item for item in FIXTURES if item["id"] == "laravel-application-logic")
    assert entry["expected_agent_id"] == "laravel-backend-expert"
    assert "laravel-eloquent-expert" in entry["excluded_alternatives"]


def test_laravel_api_design_routes_to_api_architect_not_dangling_identity():
    entry = next(item for item in FIXTURES if item["id"] == "laravel-api-contract-first")
    assert entry["expected_agent_id"] == "api-architect"
    assert "laravel-api-architect" in entry["excluded_alternatives"]


def test_django_api_request_selects_django_api_developer():
    entry = next(item for item in FIXTURES if item["id"] == "django-api-endpoints")
    assert entry["expected_agent_id"] == "django-api-developer"
    assert "django-backend-expert" in entry["excluded_alternatives"]


def test_django_orm_bottleneck_selects_orm_expert():
    entry = next(item for item in FIXTURES if item["id"] == "django-orm-bottleneck")
    assert entry["expected_agent_id"] == "django-orm-expert"


def test_rails_api_request_selects_rails_api_developer():
    entry = next(item for item in FIXTURES if item["id"] == "rails-api-endpoints")
    assert entry["expected_agent_id"] == "rails-api-developer"
    assert "rails-backend-expert" in entry["excluded_alternatives"]


def test_destructive_migration_fixture_requires_approval():
    entry = next(item for item in FIXTURES if item["id"] == "eloquent-destructive-migration")
    assert entry["expected_status"] == "needs-approval"
    assert entry["approval_policy"] == "AP-B"


def test_backend_framework_handoff_fixtures_validate():
    catalog = load_catalog(PROJECT_ROOT)
    for fixture_id in (
        "laravel-backend-delivery",
        "eloquent-work-summary",
        "django-backend-delivery",
        "django-api-delivery",
        "django-orm-report",
        "rails-backend-delivery",
        "rails-api-delivery",
        "rails-activerecord-report",
    ):
        entry = next(item for item in FIXTURES if item["id"] == fixture_id)
        validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_nineteen_profiles_are_generated():
    outputs = build_outputs(PROJECT_ROOT)
    generated = {
        path.name.removesuffix(".agent.md")
        for path in outputs
        if path.parts[:2] == (".github", "agents")
    }
    assert len(generated) == EXPECTED_PROFILE_COUNT
