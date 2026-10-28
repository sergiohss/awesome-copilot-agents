#!/usr/bin/env python3
"""One-shot builder for result-contracts.schema.json (Task 3)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/schemas/result-contracts.schema.json"

STRING_LIST = {
    "type": "array",
    "items": {"type": "string"},
}

STRING = {"type": "string"}

AGENT_ID = {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"}


def obj(*, required: list[str], properties: dict[str, object]) -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


LIST_FIELDS = {
    "assumptions",
    "allowed_agent_whitelist",
    "excluded_alternatives",
    "unresolved_prerequisites",
    "contradictions",
    "unknowns",
    "recommendations",
    "artifacts",
    "summaries",
    "grades",
    "severities",
    "positives",
    "checklist",
    "decisions",
    "questions",
    "implementer_steps",
    "endpoints",
    "components",
    "apis",
    "gems",
    "integrations",
    "consumers",
    "layers",
    "gaps",
    "controls",
    "assets",
    "threats",
}


def contract(name: str, required: list[str]) -> dict[str, object]:
    props = {
        field: STRING_LIST if field in LIST_FIELDS or field.endswith("_steps") else STRING
        for field in required
    }
    for field in ("files", "artifact_paths", "next_steps", "recommendations", "unknowns"):
        if field in required:
            props[field] = STRING_LIST
    if "stack" in required:
        props["stack"] = STRING_LIST
    if "selected_agents" in required:
        props["selected_agents"] = {
            "type": "array",
            "items": obj(
                required=["agent_id", "reason"],
                properties={"agent_id": AGENT_ID, "reason": STRING},
            ),
        }
    if "slices" in required:
        props["slices"] = {
            "type": "array",
            "items": obj(
                required=[
                    "agent_id",
                    "objective",
                    "inputs",
                    "contract_id",
                    "dependencies",
                    "artifact_paths",
                ],
                properties={
                    "agent_id": AGENT_ID,
                    "objective": STRING,
                    "inputs": STRING_LIST,
                    "contract_id": STRING,
                    "dependencies": STRING_LIST,
                    "artifact_paths": STRING_LIST,
                },
            ),
        }
    if "concurrency_groups" in required:
        props["concurrency_groups"] = {
            "type": "array",
            "items": {"type": "array", "items": AGENT_ID},
        }
    if "sections" in required:
        props["sections"] = {
            "type": "array",
            "minItems": 11,
            "maxItems": 11,
            "items": obj(
                required=["title", "summary"],
                properties={"title": STRING, "summary": STRING},
            ),
        }
    if "findings" in required:
        props["findings"] = {
            "type": "array",
            "items": obj(
                required=["summary", "evidence"],
                properties={"summary": STRING, "evidence": STRING},
            ),
        }
    if "confidence" in required:
        props["confidence"] = {"enum": ["high", "medium", "low"]}
    if "disposition" in required:
        props["disposition"] = {"enum": ["PASS", "BLOCK"]}
    if "approval_checkpoint_state" in required:
        props["approval_checkpoint_state"] = {
            "enum": ["pending", "approved", "revised", "stopped"]
        }
    if "surface_execution_mode" in required:
        props["surface_execution_mode"] = {
            "enum": ["ide-subagent", "cli-delegation", "cloud-separate-session"]
        }
    if "cloud_session_instructions" in required:
        props["cloud_session_instructions"] = {
            "type": "array",
            "items": obj(
                required=["agent_id", "instructions", "context_payload"],
                properties={
                    "agent_id": AGENT_ID,
                    "instructions": STRING,
                    "context_payload": STRING,
                },
            ),
        }
    if name == "route-plan-v1":
        props["subagent_executed"] = {"type": "boolean"}
        props["delegation_executed"] = {"type": "boolean"}
    if name == "component-delivery-v1":
        props["requires_visual_capability"] = {"type": "boolean"}
        props["requires_mcp_capability"] = {"type": "boolean"}
        props["unavailable_evidence"] = STRING
    return obj(required=required, properties=props)


CONTRACT_FIELDS: dict[str, list[str]] = {
    "route-plan-v1": [
        "request_summary",
        "assumptions",
        "slices",
        "concurrency_groups",
        "allowed_agent_whitelist",
        "excluded_alternatives",
        "approval_checkpoint_state",
        "surface_execution_mode",
        "cloud_session_instructions",
        "completion_gate",
        "unresolved_prerequisites",
    ],
    "stack-analysis-v1": [
        "stack",
        "architecture",
        "confidence",
        "findings",
        "contradictions",
        "unknowns",
        "recommendations",
    ],
    "team-configuration-v1": ["stack", "selected_agents"],
    "codebase-assessment-v1": ["sections", "confidence", "recommendations"],
    "code-review-v1": [
        "grades",
        "severities",
        "positives",
        "findings",
        "checklist",
        "disposition",
    ],
    "documentation-changelog-v1": ["artifacts", "summaries"],
    "performance-report-v1": [
        "baseline",
        "bottleneck",
        "before_after_delta",
        "recommendations",
    ],
    "api-design-report-v1": [
        "artifact",
        "decisions",
        "questions",
        "validation",
        "implementer_steps",
    ],
    "backend-implementation-v1": [
        "stack",
        "files",
        "endpoints",
        "design",
        "migrations_security",
        "tests",
        "performance",
    ],
    "frontend-implementation-v1": [
        "framework",
        "components",
        "responsiveness",
        "accessibility",
        "files",
        "next_steps",
    ],
    "component-delivery-v1": [
        "files",
        "visual_artifact",
        "checklist",
        "next_steps",
    ],
    "laravel-implementation-v1": [
        "architecture",
        "files",
        "database_ui_integration",
        "dependencies_tests_docs",
    ],
    "eloquent-work-summary-v1": [
        "models_migrations",
        "decisions",
        "evidence",
        "next_steps",
    ],
    "django-backend-implementation-v1": [
        "components",
        "features",
        "integration",
        "next_work",
        "files",
    ],
    "django-api-implementation-v1": [
        "endpoints",
        "auth",
        "serializers",
        "docs_tests",
        "integration_performance",
        "files",
    ],
    "django-orm-optimization-v1": [
        "metrics",
        "database_code_changes",
        "impact",
        "monitoring",
        "recommendations",
        "files",
    ],
    "django-fullstack-implementation-v1": [
        "apps_models_views",
        "architecture",
        "ui_admin",
        "apis_jobs",
        "files",
    ],
    "rails-backend-implementation-v1": [
        "components",
        "features",
        "integrations",
        "gems",
        "next_steps",
        "files",
    ],
    "rails-api-implementation-v1": [
        "endpoints_versioning",
        "security",
        "serialization_errors",
        "docs_tests",
        "integration",
        "files",
    ],
    "rails-activerecord-optimization-v1": [
        "metrics",
        "database_ar_changes",
        "impact",
        "recommendations",
        "files",
    ],
    "react-component-delivery-v1": [
        "boundaries",
        "server_client_choice",
        "accessibility",
        "tests_stories",
        "performance",
        "files",
    ],
    "nextjs-implementation-v1": [
        "rendering_router",
        "features",
        "performance",
        "seo",
        "integration",
        "files",
    ],
    "vue-implementation-v1": [
        "components",
        "patterns",
        "performance",
        "state_router_impact",
        "next_steps",
    ],
    "nuxt-implementation-v1": [
        "architecture",
        "features",
        "performance",
        "seo",
        "integrations",
        "files",
    ],
    "vue-state-delivery-v1": [
        "stores_actions_getters",
        "flow",
        "persistence_hydration",
        "migration",
        "consumers",
        "tests",
        "files",
    ],
    "python-implementation-v1": [
        "components",
        "features",
        "integration",
        "dependencies",
        "next_steps",
        "files",
    ],
    "fastapi-implementation-v1": [
        "apis",
        "schemas_auth",
        "architecture",
        "performance_security",
        "openapi",
        "files",
    ],
    "ml-data-implementation-v1": [
        "problem_model_metrics",
        "pipeline",
        "training",
        "production",
        "visualization",
        "files",
    ],
    "python-deployment-delivery-v1": [
        "pipeline",
        "deployment",
        "rollback",
        "credentials_gates",
        "files",
    ],
    "python-performance-report-v1": [
        "workload",
        "profiler_evidence",
        "before_after",
        "regression_disposition",
    ],
    "python-security-assessment-v1": [
        "scope",
        "assets",
        "threats",
        "severity",
        "evidence",
        "controls",
        "remediation",
        "verification",
        "disposition",
    ],
    "python-testing-delivery-v1": [
        "risk_map",
        "layers",
        "fixtures",
        "files",
        "commands_evidence",
        "coverage_mutation",
        "gaps",
    ],
    "python-acquisition-report-v1": [
        "authorization",
        "source_api_preference",
        "robots_terms_rate_controls",
        "schema",
        "validation",
        "lineage",
    ],
}


def main() -> None:
    defs = {
        contract_id: contract(contract_id, fields)
        for contract_id, fields in CONTRACT_FIELDS.items()
    }
    document = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://awesome-copilot-agents.example/schemas/result-contracts.schema.json",
        "$defs": defs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} with {len(defs)} contracts")


if __name__ == "__main__":
    main()
