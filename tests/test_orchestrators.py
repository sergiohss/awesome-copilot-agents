from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.errors import ValidationError
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/orchestrators.yaml").read_text(encoding="utf-8")
)["fixtures"]

ORCHESTRATORS = [
    (
        "tech-lead-orchestrator",
        "T-O",
        "AP-OC",
        "route-plan-v1",
        ("PROC-00", "PROC-03", "PROC-04", "PROC-05"),
        ("H",),
    ),
    (
        "project-analyst",
        "T-RX",
        "AP-R",
        "stack-analysis-v1",
        ("PROC-01", "PROC-02"),
        ("P",),
    ),
    (
        "team-configurator",
        "T-E",
        "AP-X",
        "team-configuration-v1",
        ("PROC-01", "PROC-02", "PROC-05", "PROC-20"),
        ("H", "C"),
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

BANNED_TOKENS = (
    "@agent-",
    "WriteFile",
    "model:",
    "LS",
    "CLAUDE.md",
)


@pytest.mark.parametrize("row", ORCHESTRATORS, ids=[row[0] for row in ORCHESTRATORS])
def test_orchestrator_catalog_row_matches_spec(row):
    agent_id, tool_policy, approval_policy, contract_id, procedure_ids, surfaces = row
    catalog = load_catalog(PROJECT_ROOT)
    agent = next(item for item in catalog.agents if item.id == agent_id)
    assert agent.tool_policy == tool_policy
    assert agent.approval_policy == approval_policy
    assert agent.contract_id == contract_id
    assert agent.procedure_ids == procedure_ids
    assert agent.surfaces == surfaces
    assert agent.risk_gates == ()


@pytest.mark.parametrize("agent_id", [row[0] for row in ORCHESTRATORS])
def test_orchestrator_profiles_have_required_sections(agent_id: str):
    text = (PROJECT_ROOT / "src/profiles" / f"{agent_id}.md").read_text(encoding="utf-8")
    for section in PROFILE_SECTIONS:
        assert f"## {section}" in text
    lowered = text.lower()
    for token in BANNED_TOKENS:
        assert token.lower() not in lowered, token


def test_routing_scenarios_name_expected_fields():
    scenarios = [item for item in FIXTURES if item.get("kind") == "routing"]
    assert len(scenarios) >= 3
    for entry in scenarios:
        for field in (
            "expected_agent_id",
            "excluded_alternatives",
            "approval_policy",
            "contract_id",
            "surface_mode",
            "expected_status",
        ):
            assert field in entry, entry["id"]


def test_bounded_fastapi_request_excludes_tech_lead():
    entry = next(item for item in FIXTURES if item["id"] == "bounded-fastapi-implementation")
    assert entry["expected_agent_id"] == "fastapi-expert"
    assert "tech-lead-orchestrator" in entry["excluded_alternatives"]


def test_multi_stack_architecture_request_selects_tech_lead():
    entry = next(item for item in FIXTURES if item["id"] == "multi-stack-architecture")
    assert entry["expected_agent_id"] == "tech-lead-orchestrator"
    assert entry["manual_selection"] is False


def test_team_configurator_requires_manual_selection():
    entry = next(item for item in FIXTURES if item["id"] == "team-configurator-manual")
    assert entry["expected_agent_id"] == "team-configurator"
    assert entry["manual_selection"] is True


def test_three_slice_route_plan_handoff_is_valid():
    entry = next(item for item in FIXTURES if item["id"] == "three-slice-route-plan")
    catalog = load_catalog(PROJECT_ROOT)
    validate_handoff(entry["agent_id"], entry["handoff"], catalog)
    groups = entry["handoff"]["result"]["concurrency_groups"]
    assert len(groups) == 2
    assert len(groups[0]) == 2
    assert len(groups[1]) == 1


def test_cloud_route_plan_contains_separate_session_without_execution_claim():
    entry = next(item for item in FIXTURES if item["id"] == "cloud-route-plan-orchestrator")
    catalog = load_catalog(PROJECT_ROOT)
    validate_handoff(entry["agent_id"], entry["handoff"], catalog)
    assert (
        entry["handoff"]["result"]["surface_execution_mode"] == "cloud-separate-session"
    )
    assert entry["handoff"]["result"].get("subagent_executed") is not True

    invalid = deepcopy(entry["handoff"])
    invalid["result"]["subagent_executed"] = True
    with pytest.raises(ValidationError, match=r"subagent_executed"):
        validate_handoff(entry["agent_id"], invalid, catalog)


def test_project_analyst_stack_fixture_is_valid():
    entry = next(item for item in FIXTURES if item["id"] == "project-analyst-stack-report")
    catalog = load_catalog(PROJECT_ROOT)
    validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_team_configuration_fixture_is_valid():
    entry = next(item for item in FIXTURES if item["id"] == "team-configurator-preview")
    catalog = load_catalog(PROJECT_ROOT)
    validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_orchestrator_profiles_are_generated():
    outputs = build_outputs(PROJECT_ROOT)
    for agent_id, *_ in ORCHESTRATORS:
        path = PurePosixPath(f".github/agents/{agent_id}.agent.md")
        assert path in outputs
        rendered = outputs[path].decode("utf-8")
        assert f"name: {agent_id}" in rendered
        assert "ins-core.md" not in rendered
