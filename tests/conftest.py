from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import shutil
from typing import Any, Callable

import pytest
import yaml


PROJECT_ROOT = Path(__file__).parents[1]


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
            "fragments": [],
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
