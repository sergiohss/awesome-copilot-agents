from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.errors import ValidationError
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/cross-cutting.yaml").read_text(encoding="utf-8")
)["fixtures"]


@pytest.fixture
def cross_cutting_catalog(tmp_path, minimal_catalog_tree):
    def build(agent_id: str, contract_id: str, *, tools=None, approval="AP-B", policy="T-W"):
        minimal_catalog_tree(
            tmp_path,
            extra_agent={
                "id": agent_id,
                "contract_id": contract_id,
                "tool_policy": policy,
                "approval_policy": approval,
                "tools": tools or ["read", "search", "edit", "execute"],
                "surfaces": ["H"],
            },
        )
        return load_catalog(tmp_path)

    return build


def test_shared_fragments_exist():
    fragments = [
        "ins-core.md",
        "approval-orchestrated-complex.md",
        "approval-bounded-request-is-authorization.md",
        "approval-explicit-before-external-side-effect.md",
        "approval-review-only.md",
        "handoff-v1.md",
        "surface-fallback.md",
    ]
    for name in fragments:
        path = PROJECT_ROOT / "src/fragments" / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert text.strip()


def test_cross_cutting_cloud_fixture_is_valid(cross_cutting_catalog):
    entry = next(item for item in FIXTURES if item["id"] == "cloud-route-plan-valid")
    catalog = cross_cutting_catalog(
        entry["agent_id"],
        entry["handoff"]["contract_id"],
        tools=["read", "search", "agent"],
        approval="AP-OC",
        policy="T-O",
    )
    validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_cross_cutting_cloud_execution_claim_fails(cross_cutting_catalog):
    entry = next(item for item in FIXTURES if item["id"] == "cloud-route-plan-execution-claim")
    base = next(item for item in FIXTURES if item["id"] == "cloud-route-plan-valid")
    payload = deepcopy(base["handoff"])
    payload["result"]["subagent_executed"] = True
    catalog = cross_cutting_catalog(
        entry["agent_id"],
        payload["contract_id"],
        tools=["read", "search", "agent"],
        approval="AP-OC",
        policy="T-O",
    )
    with pytest.raises(ValidationError, match=r"subagent_executed"):
        validate_handoff(entry["agent_id"], payload, catalog)


def test_unavailable_visual_requires_evidence_or_blocked(cross_cutting_catalog):
    needs_evidence = next(
        item for item in FIXTURES if item["id"] == "unavailable-visual-requires-evidence"
    )
    catalog = cross_cutting_catalog(
        needs_evidence["agent_id"],
        needs_evidence["handoff"]["contract_id"],
    )
    with pytest.raises(ValidationError, match=r"unavailable_evidence"):
        validate_handoff(needs_evidence["agent_id"], needs_evidence["handoff"], catalog)

    blocked = next(item for item in FIXTURES if item["id"] == "unavailable-visual-blocked")
    catalog_blocked = cross_cutting_catalog(
        blocked["agent_id"],
        blocked["handoff"]["contract_id"],
    )
    validate_handoff(blocked["agent_id"], blocked["handoff"], catalog_blocked)


def test_surface_fallback_fragment_documents_two_agent_cap():
    text = (PROJECT_ROOT / "src/fragments/surface-fallback.md").read_text(encoding="utf-8")
    assert "two" in text.lower()
    assert "cloud-separate-session" in text
