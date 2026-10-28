from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from pathlib import Path
import shutil
from typing import Any, Callable

import pytest
import yaml


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "tests/fixtures/minimal"


@dataclass(frozen=True, slots=True)
class MinimalProject:
    root: Path
    profile: Path
    fragment: Path
    output: Path

    def _update_agent(self, field: str, value: object) -> None:
        path = self.root / "src/catalog/agents.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["agents"][0][field] = value
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    def set_tools(self, tools: list[str]) -> None:
        self._update_agent("tools", tools)

    def set_fragments(self, fragments: list[str]) -> None:
        self._update_agent("fragments", fragments)


@pytest.fixture
def minimal_catalog_tree() -> Callable[..., None]:
    def write_catalog(
        root: Path,
        *,
        tools: list[str] | None = None,
        extra_agent: dict[str, Any] | None = None,
        duplicate_agent: bool = False,
        profile: str = "src/agents/project-analyst.agent.md",
        contract_id: str = "stack-analysis-v1",
        procedure_ids: list[str] | None = None,
        fragments: list[str] | None = None,
        path_specific: list[dict[str, object]] | None = None,
    ) -> None:
        catalog_dir = root / "src/catalog"
        schema_dir = root / "src/schemas"
        catalog_dir.mkdir(parents=True)
        schema_dir.mkdir(parents=True)
        shutil.copy2(PROJECT_ROOT / "src/schemas/catalog.schema.json", schema_dir)

        agent = {
            "id": "project-analyst",
            "description": "Inspect an unfamiliar repository and report evidence.",
            "tools": tools if tools is not None else ["read", "search", "execute"],
            "tool_policy": "T-RX",
            "approval_policy": "AP-R",
            "risk_gates": [],
            "surfaces": ["P"],
            "contract_id": contract_id,
            "procedure_ids": procedure_ids if procedure_ids is not None else ["PROC-01"],
            "profile": profile,
            "fragments": fragments if fragments is not None else [],
        }
        agent.update(extra_agent or {})
        agents = [agent, deepcopy(agent)] if duplicate_agent else [agent]

        files = {
            "agents.yaml": {"agents": agents},
            "procedures.yaml": {
                "procedures": [
                    {
                        "id": "PROC-01",
                        "skill_name": "aca-inventory-first-discovery",
                        "contract": "Establish evidence-backed inventory before conclusions",
                    }
                ]
            },
            "contracts.yaml": {"contracts": {"stack-analysis-v1": "Stack analysis result"}},
            "instructions.yaml": {
                "repository": "src/instructions/copilot.md",
                "path_specific": path_specific if path_specific is not None else [],
            },
        }
        for name, document in files.items():
            (catalog_dir / name).write_text(
                yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
            )

    return write_catalog


@pytest.fixture
def minimal_project(
    tmp_path: Path,
    minimal_catalog_tree: Callable[..., None],
) -> MinimalProject:
    shutil.copytree(FIXTURE_ROOT, tmp_path, dirs_exist_ok=True)
    minimal_catalog_tree(
        tmp_path,
        profile="src/profiles/project-analyst.md",
        fragments=["src/fragments/ins-core.md"],
    )
    schema_dir = tmp_path / "src/schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_ROOT / "src/schemas/source-baseline.schema.json", schema_dir)
    instruction = tmp_path / "src/instructions/copilot.md"
    instruction.parent.mkdir(parents=True)
    instruction.write_text("Use repository evidence first.\n", encoding="utf-8")
    output = tmp_path / ".github/agents/project-analyst.agent.md"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"existing output\n")
    return MinimalProject(
        root=tmp_path,
        profile=tmp_path / "src/profiles/project-analyst.md",
        fragment=tmp_path / "src/fragments/ins-core.md",
        output=output,
    )
