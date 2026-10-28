from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from aca_tools.contracts import primary_contract_ids, validate_handoff
from aca_tools.errors import ValidationError
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]

EXPECTED_CONTRACTS = frozenset(
    {
        "route-plan-v1",
        "stack-analysis-v1",
        "team-configuration-v1",
        "codebase-assessment-v1",
        "code-review-v1",
        "documentation-changelog-v1",
        "performance-report-v1",
        "api-design-report-v1",
        "backend-implementation-v1",
        "frontend-implementation-v1",
        "component-delivery-v1",
        "laravel-implementation-v1",
        "eloquent-work-summary-v1",
        "django-backend-implementation-v1",
        "django-api-implementation-v1",
        "django-orm-optimization-v1",
        "django-fullstack-implementation-v1",
        "rails-backend-implementation-v1",
        "rails-api-implementation-v1",
        "rails-activerecord-optimization-v1",
        "react-component-delivery-v1",
        "nextjs-implementation-v1",
        "vue-implementation-v1",
        "nuxt-implementation-v1",
        "vue-state-delivery-v1",
        "python-implementation-v1",
        "fastapi-implementation-v1",
        "ml-data-implementation-v1",
        "python-deployment-delivery-v1",
        "python-performance-report-v1",
        "python-security-assessment-v1",
        "python-testing-delivery-v1",
        "python-acquisition-report-v1",
    }
)

VALID = {
    "handoff_version": 1,
    "contract_id": "stack-analysis-v1",
    "status": "completed",
    "summary": "Detected Python and FastAPI from pyproject.toml.",
    "artifact_paths": [],
    "routing": {
        "recommended_next_agent": None,
        "reason": "Exact framework owner",
        "prerequisites": [],
    },
    "result": {
        "stack": ["Python", "FastAPI"],
        "architecture": "service monolith",
        "confidence": "high",
        "findings": [
            {
                "summary": "FastAPI declared in pyproject.toml",
                "evidence": "pyproject.toml",
            }
        ],
        "contradictions": [],
        "unknowns": [],
        "recommendations": ["fastapi-expert"],
    },
}


def test_primary_contract_catalog_covers_all_thirty_three():
    catalog = load_catalog(PROJECT_ROOT)
    assert EXPECTED_CONTRACTS == primary_contract_ids()
    assert EXPECTED_CONTRACTS == frozenset(catalog.contracts.keys())


def test_validate_handoff_accepts_valid_stack_analysis(tmp_path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    catalog = load_catalog(tmp_path)
    validate_handoff("project-analyst", VALID, catalog)


def test_handoff_rejects_missing_status(tmp_path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    catalog = load_catalog(tmp_path)
    payload = dict(VALID)
    del payload["status"]
    with pytest.raises(ValidationError, match=r"status"):
        validate_handoff("project-analyst", payload, catalog)


def test_routing_rejects_unknown_next_agent(tmp_path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    catalog = load_catalog(tmp_path)
    payload = deepcopy(VALID)
    payload["routing"] = {
        "recommended_next_agent": "fastapi-expert",
        "reason": "Exact framework owner",
        "prerequisites": [],
    }
    with pytest.raises(ValidationError, match=r"recommended_next_agent.*fastapi-expert"):
        validate_handoff("project-analyst", payload, catalog)


def test_route_plan_rejects_concurrency_group_over_two(tmp_path, minimal_catalog_tree):
    minimal_catalog_tree(
        tmp_path,
        extra_agent={
            "id": "tech-lead-orchestrator",
            "contract_id": "route-plan-v1",
            "tool_policy": "T-O",
            "approval_policy": "AP-OC",
            "tools": ["read", "search", "agent"],
            "surfaces": ["H"],
        },
    )
    catalog = load_catalog(tmp_path)
    payload = {
        "handoff_version": 1,
        "contract_id": "route-plan-v1",
        "status": "completed",
        "summary": "Plan with invalid concurrency",
        "artifact_paths": [],
        "routing": {
            "recommended_next_agent": None,
            "reason": None,
            "prerequisites": [],
        },
        "result": {
            "request_summary": "Parallel refactor",
            "assumptions": [],
            "slices": [],
            "concurrency_groups": [["a-one", "a-two", "a-three"]],
            "allowed_agent_whitelist": [],
            "excluded_alternatives": [],
            "approval_checkpoint_state": "approved",
            "surface_execution_mode": "cloud-separate-session",
            "cloud_session_instructions": [],
            "completion_gate": "Review",
            "unresolved_prerequisites": [],
        },
    }
    with pytest.raises(ValidationError, match=r"at most two agents"):
        validate_handoff("tech-lead-orchestrator", payload, catalog)


def test_cloud_route_plan_rejects_execution_claim(tmp_path, minimal_catalog_tree):
    minimal_catalog_tree(
        tmp_path,
        extra_agent={
            "id": "tech-lead-orchestrator",
            "contract_id": "route-plan-v1",
            "tool_policy": "T-O",
            "approval_policy": "AP-OC",
            "tools": ["read", "search", "agent"],
            "surfaces": ["H"],
        },
    )
    catalog = load_catalog(tmp_path)
    payload = {
        "handoff_version": 1,
        "contract_id": "route-plan-v1",
        "status": "completed",
        "summary": "Invalid cloud execution claim",
        "artifact_paths": [],
        "routing": {
            "recommended_next_agent": None,
            "reason": None,
            "prerequisites": [],
        },
        "result": {
            "request_summary": "Cloud plan",
            "assumptions": [],
            "slices": [],
            "concurrency_groups": [],
            "allowed_agent_whitelist": [],
            "excluded_alternatives": [],
            "approval_checkpoint_state": "approved",
            "surface_execution_mode": "cloud-separate-session",
            "cloud_session_instructions": [],
            "completion_gate": "Review",
            "unresolved_prerequisites": [],
            "subagent_executed": True,
        },
    }
    with pytest.raises(ValidationError, match=r"subagent_executed"):
        validate_handoff("tech-lead-orchestrator", payload, catalog)
