from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/python-application.yaml").read_text(encoding="utf-8")
)["fixtures"]

PYTHON_APPLICATION = [
    (
        "python-expert",
        "python-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "fastapi-expert",
        "fastapi-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-08", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "django-expert",
        "django-fullstack-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09"),
        ("H", "D"),
        (),
    ),
    (
        "ml-data-expert",
        "ml-data-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09", "PROC-18"),
        ("H", "D"),
        ("external-model-or-data-side-effect",),
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

FILENAME_ERA_FORBIDDEN_PUBLIC_IDS = frozenset(
    {
        "devops-cicd-expert",
        "performance-expert",
        "security-expert",
        "testing-expert",
        "web-scraping-expert",
    }
)

EXPECTED_PYTHON_APPLICATION_IDS = {row[0] for row in PYTHON_APPLICATION}
EXPECTED_PROFILE_COUNT = 33


@pytest.mark.parametrize("row", PYTHON_APPLICATION, ids=[row[0] for row in PYTHON_APPLICATION])
def test_python_application_catalog_row_matches_spec(row):
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


@pytest.mark.parametrize("agent_id", [row[0] for row in PYTHON_APPLICATION])
def test_python_application_profiles_have_required_sections(agent_id: str):
    text = (PROJECT_ROOT / "src/profiles" / f"{agent_id}.md").read_text(encoding="utf-8")
    for section in PROFILE_SECTIONS:
        assert f"## {section}" in text


def test_python_application_public_ids_are_exact_corrected_set():
    catalog = load_catalog(PROJECT_ROOT)
    public_ids = {agent.id for agent in catalog.agents}
    assert EXPECTED_PYTHON_APPLICATION_IDS <= public_ids
    assert public_ids.isdisjoint(FILENAME_ERA_FORBIDDEN_PUBLIC_IDS)


def test_fastapi_pydantic_async_selects_fastapi_expert():
    entry = next(item for item in FIXTURES if item["id"] == "fastapi-async-pydantic-api")
    assert entry["expected_agent_id"] == "fastapi-expert"
    assert "python-expert" in entry["excluded_alternatives"]
    assert "backend-developer" in entry["excluded_alternatives"]


def test_cross_cutting_django_selects_fullstack_expert():
    entry = next(item for item in FIXTURES if item["id"] == "django-fullstack-admin-celery")
    assert entry["expected_agent_id"] == "django-expert"
    assert "django-backend-expert" in entry["excluded_alternatives"]
    assert "django-api-developer" in entry["excluded_alternatives"]


def test_general_python_cli_selects_python_expert():
    entry = next(item for item in FIXTURES if item["id"] == "general-python-packaging-cli")
    assert entry["expected_agent_id"] == "python-expert"
    assert "fastapi-expert" in entry["excluded_alternatives"]


def test_ml_training_pipeline_selects_ml_data_expert():
    entry = next(item for item in FIXTURES if item["id"] == "ml-training-serving-pipeline")
    assert entry["expected_agent_id"] == "ml-data-expert"
    assert "python-expert" in entry["excluded_alternatives"]


def test_external_model_download_requires_approval():
    entry = next(item for item in FIXTURES if item["id"] == "ml-external-model-registry-pull")
    assert entry["expected_status"] == "needs-approval"
    assert entry["expected_agent_id"] == "ml-data-expert"
    assert entry["approval_policy"] == "AP-B"


def test_python_application_handoff_fixtures_validate():
    catalog = load_catalog(PROJECT_ROOT)
    for fixture_id in (
        "python-implementation-delivery",
        "fastapi-implementation-delivery",
        "django-fullstack-delivery",
        "ml-data-implementation-delivery",
    ):
        entry = next(item for item in FIXTURES if item["id"] == fixture_id)
        validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_thirty_three_profiles_include_python_application_agents():
    outputs = build_outputs(PROJECT_ROOT)
    generated = {
        path.name.removesuffix(".agent.md")
        for path in outputs
        if path.parts[:2] == (".github", "agents")
    }
    assert len(generated) == EXPECTED_PROFILE_COUNT
    assert EXPECTED_PYTHON_APPLICATION_IDS <= generated
