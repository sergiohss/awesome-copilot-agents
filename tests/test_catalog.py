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


def test_catalog_models_are_immutable(tmp_path: Path, minimal_catalog_tree):
    minimal_catalog_tree(tmp_path)
    catalog = load_catalog(tmp_path)
    with pytest.raises(FrozenInstanceError):
        catalog.agents[0].id = "changed"  # type: ignore[misc]


def test_repository_catalog_has_strict_task_one_skeleton():
    root = Path(__file__).parents[1]
    catalog = load_catalog(root)
    assert catalog.agents == ()
    assert len(catalog.procedures) == 21
    assert [procedure.id for procedure in catalog.procedures] == [
        f"PROC-{index:02d}" for index in range(21)
    ]
    assert catalog.contracts == {}
    assert catalog.instructions.repository.as_posix() == "src/instructions/copilot.md"
    assert catalog.instructions.path_specific == ()
