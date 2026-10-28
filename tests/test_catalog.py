from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aca_tools.errors import ValidationError
from aca_tools.loaders import load_catalog


def test_catalog_rejects_unknown_tool(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, tools=["read", "teleport"])
    with pytest.raises(ValidationError, match=r"agents\[0\]\.tools\[1\].*teleport"):
        load_catalog(tmp_path)


def test_catalog_rejects_unknown_agent_key(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, extra_agent={"temperature": 0.2})
    with pytest.raises(ValidationError, match=r"temperature"):
        load_catalog(tmp_path)


def test_catalog_requires_unique_public_ids(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, duplicate_agent=True)
    with pytest.raises(ValidationError, match=r"duplicate agent id: project-analyst"):
        load_catalog(tmp_path)


def test_catalog_rejects_yaml_aliases(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    (tmp_path / "src/catalog/agents.yaml").write_text(
        "agents:\n  - &agent\n    id: project-analyst\n  - *agent\n", encoding="utf-8"
    )
    with pytest.raises(ValidationError, match=r"agents\.yaml.*aliases"):
        load_catalog(tmp_path)


def test_catalog_rejects_duplicate_yaml_keys(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    (tmp_path / "src/catalog/agents.yaml").write_text(
        "agents: []\nagents: []\n", encoding="utf-8"
    )
    with pytest.raises(ValidationError, match=r"agents\.yaml.*duplicate YAML key: agents"):
        load_catalog(tmp_path)


def test_catalog_rejects_custom_yaml_tags(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    (tmp_path / "src/catalog/agents.yaml").write_text(
        "agents: !unsafe []\n", encoding="utf-8"
    )
    with pytest.raises(ValidationError, match=r"agents\.yaml.*custom YAML tag"):
        load_catalog(tmp_path)


@pytest.mark.parametrize("profile", ["/tmp/agent.md", "../agent.md", r"src\\agent.md"])
def test_catalog_rejects_non_posix_relative_profile_paths(
    tmp_path: Path, minimal_catalog_tree, profile: str
):
    minimal_catalog_tree(tmp_path, profile=profile)
    with pytest.raises(ValidationError, match=r"agents\[0\]\.profile"):
        load_catalog(tmp_path)


def test_catalog_enforces_static_tool_policy_expansion(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, tools=["read", "search"])
    with pytest.raises(ValidationError, match=r"agents\[0\]\.tools.*T-RX"):
        load_catalog(tmp_path)


def test_catalog_validates_cross_links(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path, procedure_ids=["PROC-20"])
    with pytest.raises(ValidationError, match=r"agents\[0\]\.procedure_ids\[0\].*PROC-20"):
        load_catalog(tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("instruction", "/tmp/python.md"),
        ("instruction", "../python.md"),
        ("instruction", r"src\instructions\python.md"),
        ("instruction", "C:/src/instructions/python.md"),
        ("apply_to", "/src/**/*.py"),
        ("apply_to", "../**/*.py"),
        ("apply_to", r"src\**\*.py"),
        ("apply_to", "C:/src/**/*.py"),
    ],
)
def test_catalog_rejects_nonportable_path_specific_entries(
    tmp_path: Path, minimal_catalog_tree, field: str, value: str
):
    entry = {
        "apply_to": "**/*.py",
        "instruction": "src/instructions/python.md",
    }
    entry[field] = value
    minimal_catalog_tree(tmp_path, path_specific=[entry])
    with pytest.raises(
        ValidationError,
        match=rf"instructions\.path_specific\[0\]\.{field}",
    ):
        load_catalog(tmp_path)


def test_catalog_accepts_portable_path_specific_entry(tmp_path: Path, minimal_catalog_tree):
    entry = {
        "apply_to": "**/*.py",
        "instruction": "src/instructions/python.md",
    }
    minimal_catalog_tree(tmp_path, path_specific=[entry])
    assert dict(load_catalog(tmp_path).instructions.path_specific[0]) == entry


def test_catalog_models_are_immutable(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    catalog = load_catalog(tmp_path)
    with pytest.raises(FrozenInstanceError):
        catalog.agents[0].id = "changed"  # type: ignore[misc]


def test_repository_catalog_has_orchestrator_core_and_universal_agents():
    root = Path(__file__).parents[1]
    catalog = load_catalog(root)
    assert {agent.id for agent in catalog.agents} == {
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
        "laravel-backend-expert",
        "laravel-eloquent-expert",
        "django-backend-expert",
        "django-api-developer",
        "django-orm-expert",
        "rails-backend-expert",
        "rails-api-developer",
        "rails-activerecord-expert",
        "react-component-architect",
        "react-nextjs-expert",
        "vue-component-architect",
        "vue-nuxt-expert",
        "vue-state-manager",
        "python-expert",
        "fastapi-expert",
        "django-expert",
        "ml-data-expert",
        "python-devops-cicd-expert",
        "python-performance-expert",
        "python-security-expert",
        "python-testing-expert",
        "python-web-scraping-expert",
    }
    assert len(catalog.procedures) == 21
    assert [procedure.id for procedure in catalog.procedures] == [
        f"PROC-{index:02d}" for index in range(21)
    ]
    assert len(catalog.contracts) == 33
    assert "stack-analysis-v1" in catalog.contracts
    assert catalog.instructions.repository.as_posix() == "src/instructions/copilot.md"
    assert catalog.instructions.path_specific == ()
