from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/python-operations.yaml").read_text(encoding="utf-8")
)["fixtures"]

PYTHON_OPERATIONS = [
    (
        "python-devops-cicd-expert",
        "python-deployment-delivery-v1",
        ("PROC-07", "PROC-09", "PROC-17"),
        ("H",),
        ("deployment", "credentials", "destructive-infrastructure"),
        "T-W",
        "AP-X",
        ("read", "search", "edit", "execute"),
    ),
    (
        "python-performance-expert",
        "python-performance-report-v1",
        ("PROC-11",),
        ("H",),
        (),
        "T-W",
        "AP-B",
        ("read", "search", "edit", "execute"),
    ),
    (
        "python-security-expert",
        "python-security-assessment-v1",
        ("PROC-12", "PROC-16"),
        ("H",),
        ("credential-bearing-scans",),
        "T-RX",
        "AP-R",
        ("read", "search", "execute"),
    ),
    (
        "python-testing-expert",
        "python-testing-delivery-v1",
        ("PROC-15",),
        ("H",),
        (),
        "T-W",
        "AP-B",
        ("read", "search", "edit", "execute"),
    ),
    (
        "python-web-scraping-expert",
        "python-acquisition-report-v1",
        ("PROC-19",),
        ("D", "V"),
        ("authorization", "credentials", "acquisition"),
        "T-W",
        "AP-X",
        ("read", "search", "edit", "execute"),
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

EXPECTED_OPERATIONS_IDS = {row[0] for row in PYTHON_OPERATIONS}
EXPECTED_PROFILE_COUNT = 33


@pytest.mark.parametrize("row", PYTHON_OPERATIONS, ids=[row[0] for row in PYTHON_OPERATIONS])
def test_python_operations_catalog_row_matches_spec(row):
    (
        agent_id,
        contract_id,
        procedure_ids,
        surfaces,
        risk_gates,
        tool_policy,
        approval_policy,
        tools,
    ) = row
    catalog = load_catalog(PROJECT_ROOT)
    agent = next(item for item in catalog.agents if item.id == agent_id)
    assert agent.tool_policy == tool_policy
    assert agent.approval_policy == approval_policy
    assert agent.contract_id == contract_id
    assert agent.procedure_ids == procedure_ids
    assert agent.surfaces == surfaces
    assert agent.risk_gates == risk_gates
    assert tuple(agent.tools) == tools


@pytest.mark.parametrize("agent_id", [row[0] for row in PYTHON_OPERATIONS])
def test_python_operations_profiles_have_required_sections(agent_id: str):
    text = (PROJECT_ROOT / "src/profiles" / f"{agent_id}.md").read_text(encoding="utf-8")
    for section in PROFILE_SECTIONS:
        assert f"## {section}" in text


def test_python_security_profile_is_assessment_only():
    text = (PROJECT_ROOT / "src/profiles/python-security-expert.md").read_text(encoding="utf-8").lower()
    assert "read-only" in text or "does not remediate" in text
    assert "remediate" in text


def test_devops_and_acquisition_fixtures_require_manual_selection():
    devops = next(item for item in FIXTURES if item["id"] == "python-cicd-rollout-manual")
    acquisition = next(item for item in FIXTURES if item["id"] == "authorized-data-acquisition-manual")
    assert devops["manual_selection"] is True
    assert acquisition["manual_selection"] is True


def test_unauthorized_acquisition_requires_approval():
    entry = next(item for item in FIXTURES if item["id"] == "missing-acquisition-authorization")
    assert entry["expected_agent_id"] == "python-web-scraping-expert"
    assert entry["expected_status"] == "needs-approval"
    assert entry["approval_policy"] == "AP-X"


def test_python_runtime_profiling_selects_performance_expert():
    entry = next(item for item in FIXTURES if item["id"] == "python-runtime-profiling")
    assert entry["expected_agent_id"] == "python-performance-expert"
    assert "performance-optimizer" in entry["excluded_alternatives"]


def test_python_operations_handoff_fixtures_validate():
    catalog = load_catalog(PROJECT_ROOT)
    for fixture_id in (
        "python-deployment-delivery",
        "python-performance-report",
        "python-security-assessment",
        "python-testing-delivery",
        "python-acquisition-report",
    ):
        entry = next(item for item in FIXTURES if item["id"] == fixture_id)
        validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_thirty_three_profiles_are_generated_with_unique_names():
    outputs = build_outputs(PROJECT_ROOT)
    generated = {
        path.name.removesuffix(".agent.md")
        for path in outputs
        if path.parts[:2] == (".github", "agents")
    }
    assert len(generated) == EXPECTED_PROFILE_COUNT
    assert EXPECTED_OPERATIONS_IDS <= generated

    names: list[str] = []
    for agent_id in sorted(generated):
        text = (PROJECT_ROOT / ".github/agents" / f"{agent_id}.agent.md").read_text(encoding="utf-8")
        match = re.match(r"^---\nname:\s*(.+?)\n", text)
        assert match, agent_id
        names.append(match.group(1).strip())
    assert len(names) == len(set(names))
