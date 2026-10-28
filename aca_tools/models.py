from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping


@dataclass(frozen=True, slots=True)
class AgentSpec:
    id: str
    description: str
    tools: tuple[str, ...]
    tool_policy: str
    approval_policy: str
    risk_gates: tuple[str, ...]
    surfaces: tuple[str, ...]
    contract_id: str
    procedure_ids: tuple[str, ...]
    profile: PurePosixPath
    fragments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProcedureSpec:
    id: str
    skill_name: str
    contract: str


@dataclass(frozen=True, slots=True)
class InstructionCatalog:
    repository: PurePosixPath
    path_specific: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class Catalog:
    agents: tuple[AgentSpec, ...]
    procedures: tuple[ProcedureSpec, ...]
    contracts: Mapping[str, str]
    instructions: InstructionCatalog
