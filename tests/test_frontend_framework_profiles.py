from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aca_tools.contracts import validate_handoff
from aca_tools.generate import build_outputs
from aca_tools.loaders import load_catalog


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES = yaml.safe_load(
    (PROJECT_ROOT / "src/routing-fixtures/frontend-frameworks.yaml").read_text(encoding="utf-8")
)["fixtures"]

FRONTEND_FRAMEWORK = [
    (
        "react-component-architect",
        "react-component-delivery-v1",
        ("PROC-06", "PROC-07", "PROC-09", "PROC-14"),
        ("H", "D", "V"),
        (),
    ),
    (
        "react-nextjs-expert",
        "nextjs-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09", "PROC-14"),
        ("H", "D", "V"),
        (),
    ),
    (
        "vue-component-architect",
        "vue-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09", "PROC-14"),
        ("H", "D", "V"),
        (),
    ),
    (
        "vue-nuxt-expert",
        "nuxt-implementation-v1",
        ("PROC-06", "PROC-07", "PROC-09", "PROC-14"),
        ("H", "D", "V"),
        (),
    ),
    (
        "vue-state-manager",
        "vue-state-delivery-v1",
        ("PROC-06", "PROC-07"),
        ("H", "D"),
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

VUE_STATE_RESULT_FIELDS = (
    "stores_actions_getters",
    "flow",
    "persistence_hydration",
    "migration",
    "consumers",
    "tests",
    "files",
)

EXPECTED_PROFILE_COUNT = 33


@pytest.mark.parametrize("row", FRONTEND_FRAMEWORK, ids=[row[0] for row in FRONTEND_FRAMEWORK])
def test_frontend_framework_catalog_row_matches_spec(row):
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


@pytest.mark.parametrize("agent_id", [row[0] for row in FRONTEND_FRAMEWORK])
def test_frontend_framework_profiles_have_required_sections(agent_id: str):
    text = (PROJECT_ROOT / "src/profiles" / f"{agent_id}.md").read_text(encoding="utf-8")
    for section in PROFILE_SECTIONS:
        assert f"## {section}" in text


def test_react_hooks_select_component_architect_not_nextjs():
    entry = next(item for item in FIXTURES if item["id"] == "react-hooks-component-library")
    assert entry["expected_agent_id"] == "react-component-architect"
    assert "react-nextjs-expert" in entry["excluded_alternatives"]
    assert "frontend-developer" in entry["excluded_alternatives"]


def test_next_routing_cache_selects_nextjs_expert():
    entry = next(item for item in FIXTURES if item["id"] == "next-app-router-cache")
    assert entry["expected_agent_id"] == "react-nextjs-expert"
    assert "react-component-architect" in entry["excluded_alternatives"]


def test_vue_composables_select_component_architect():
    entry = next(item for item in FIXTURES if item["id"] == "vue-composable-components")
    assert entry["expected_agent_id"] == "vue-component-architect"
    assert "vue-nuxt-expert" in entry["excluded_alternatives"]
    assert "vue-state-manager" in entry["excluded_alternatives"]


def test_nuxt_nitro_seo_selects_nuxt_expert():
    entry = next(item for item in FIXTURES if item["id"] == "nuxt-nitro-ssr-seo")
    assert entry["expected_agent_id"] == "vue-nuxt-expert"
    assert "vue-component-architect" in entry["excluded_alternatives"]


def test_pinia_persistence_hydration_selects_state_manager():
    entry = next(item for item in FIXTURES if item["id"] == "pinia-ssr-hydration")
    assert entry["expected_agent_id"] == "vue-state-manager"
    assert "vue-component-architect" in entry["excluded_alternatives"]


def test_vue_state_profile_documents_semantic_repair_not_duplicated_source():
    text = (PROJECT_ROOT / "src/profiles/vue-state-manager.md").read_text(encoding="utf-8")
    assert "VUE-03-SEMANTIC-REPAIR" in text
    lowered = text.lower()
    assert "duplicate" in lowered or "not derived from duplicated source" in lowered
    assert "pinia" in lowered
    assert "vuex" in lowered


def test_vue_state_result_contract_lists_required_typed_fields():
    text = (PROJECT_ROOT / "src/profiles/vue-state-manager.md").read_text(encoding="utf-8")
    for field in VUE_STATE_RESULT_FIELDS:
        assert field in text


def test_frontend_framework_handoff_fixtures_validate():
    catalog = load_catalog(PROJECT_ROOT)
    for fixture_id in (
        "react-component-delivery",
        "nextjs-implementation-delivery",
        "vue-implementation-delivery",
        "nuxt-implementation-delivery",
        "vue-state-delivery",
    ):
        entry = next(item for item in FIXTURES if item["id"] == fixture_id)
        validate_handoff(entry["agent_id"], entry["handoff"], catalog)


def test_thirty_three_profiles_include_frontend_agents():
    outputs = build_outputs(PROJECT_ROOT)
    generated = {
        path.name.removesuffix(".agent.md")
        for path in outputs
        if path.parts[:2] == (".github", "agents")
    }
    assert len(generated) == EXPECTED_PROFILE_COUNT
