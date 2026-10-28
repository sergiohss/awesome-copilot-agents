from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from yaml.tokens import AliasToken, AnchorToken, TagToken

from .errors import ValidationError
from .models import AgentSpec, Catalog, InstructionCatalog, ProcedureSpec


_TOOL_POLICIES: dict[str, tuple[str, ...]] = {
    "T-R": ("read", "search"),
    "T-RX": ("read", "search", "execute"),
    "T-O": ("read", "search", "agent"),
    "T-E": ("read", "search", "edit"),
    "T-W": ("read", "search", "edit", "execute"),
}


def _field_path(parts: list[object]) -> str:
    result = ""
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += ("." if result else "") + str(part)
    return result or "catalog"


def _reject_duplicate_keys(node: Node | None, filename: str) -> None:
    if isinstance(node, MappingNode):
        seen: set[tuple[str, str]] = set()
        for key, value in node.value:
            if isinstance(key, ScalarNode):
                identity = (key.tag, key.value)
                if identity in seen:
                    raise ValidationError(
                        f"{filename}: duplicate YAML key: {key.value}"
                    )
                seen.add(identity)
            _reject_duplicate_keys(key, filename)
            _reject_duplicate_keys(value, filename)
    elif isinstance(node, SequenceNode):
        for item in node.value:
            _reject_duplicate_keys(item, filename)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValidationError(f"{path.name}: cannot read UTF-8 YAML: {error}") from error
    try:
        for token in yaml.scan(text):
            if isinstance(token, (AliasToken, AnchorToken)):
                raise ValidationError(f"{path.name}: YAML aliases and anchors are not allowed")
            if isinstance(token, TagToken):
                raise ValidationError(f"{path.name}: custom YAML tags are not allowed")
        _reject_duplicate_keys(yaml.compose(text, Loader=yaml.SafeLoader), path.name)
        document = yaml.safe_load(text)
    except ValidationError:
        raise
    except yaml.YAMLError as error:
        raise ValidationError(f"{path.name}: invalid YAML: {error}") from error
    if not isinstance(document, dict):
        raise ValidationError(f"{path.name}: document must be a mapping")
    return document


def _posix_relative(value: str, field: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or ":" in value
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ValidationError(f"{field}: must be a normalized POSIX relative path")
    return path


def _validate_schema(root: Path, document: dict[str, Any]) -> None:
    schema_path = root / "src/schemas/catalog.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"catalog schema: cannot load {schema_path}: {error}") from error
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        raise ValidationError(f"{_field_path(list(error.absolute_path))}: {error.message}")


def load_catalog(root: Path) -> Catalog:
    """Load four canonical catalogs, validate JSON Schema, cross-links, IDs, and static tools."""
    catalog_dir = root / "src/catalog"
    documents = {
        name: _load_yaml(catalog_dir / f"{name}.yaml")
        for name in ("agents", "procedures", "contracts", "instructions")
    }
    combined: dict[str, Any] = {}
    for name in ("agents", "procedures", "contracts"):
        document = documents[name]
        if set(document) != {name}:
            extras = sorted(set(document) - {name})
            missing = name not in document
            detail = f"unknown key {extras[0]}" if extras else f"missing key {name}"
            if missing and extras:
                detail = f"missing key {name}; {detail}"
            raise ValidationError(f"{name}.yaml: {detail}")
        combined[name] = document[name]
    combined["instructions"] = documents["instructions"]
    _validate_schema(root, combined)

    agents_raw: list[dict[str, Any]] = combined["agents"]
    procedures_raw: list[dict[str, Any]] = combined["procedures"]
    contracts_raw: dict[str, str] = combined["contracts"]
    instructions_raw: dict[str, Any] = combined["instructions"]

    seen_agents: set[str] = set()
    seen_profiles: set[PurePosixPath] = set()
    procedure_ids: set[str] = set()
    for index, procedure in enumerate(procedures_raw):
        procedure_id = procedure["id"]
        if procedure_id in procedure_ids:
            raise ValidationError(f"duplicate procedure id: {procedure_id}")
        procedure_ids.add(procedure_id)

    agents: list[AgentSpec] = []
    for index, agent in enumerate(agents_raw):
        agent_id = agent["id"]
        if agent_id in seen_agents:
            raise ValidationError(f"duplicate agent id: {agent_id}")
        seen_agents.add(agent_id)
        expected_tools = _TOOL_POLICIES[agent["tool_policy"]]
        if tuple(agent["tools"]) != expected_tools:
            raise ValidationError(
                f"agents[{index}].tools: must exactly expand {agent['tool_policy']} as {list(expected_tools)}"
            )
        profile = _posix_relative(agent["profile"], f"agents[{index}].profile")
        if profile in seen_profiles:
            raise ValidationError(f"agents[{index}].profile: duplicate profile path {profile}")
        seen_profiles.add(profile)
        fragments = tuple(
            _posix_relative(fragment, f"agents[{index}].fragments[{fragment_index}]").as_posix()
            for fragment_index, fragment in enumerate(agent["fragments"])
        )
        contract_id = agent["contract_id"]
        if contract_id not in contracts_raw:
            raise ValidationError(f"agents[{index}].contract_id: unknown contract {contract_id}")
        for procedure_index, procedure_id in enumerate(agent["procedure_ids"]):
            if procedure_id not in procedure_ids:
                raise ValidationError(
                    f"agents[{index}].procedure_ids[{procedure_index}]: unknown procedure {procedure_id}"
                )
        agents.append(
            AgentSpec(
                id=agent_id,
                description=agent["description"],
                tools=tuple(agent["tools"]),
                tool_policy=agent["tool_policy"],
                approval_policy=agent["approval_policy"],
                risk_gates=tuple(agent["risk_gates"]),
                surfaces=tuple(agent["surfaces"]),
                contract_id=contract_id,
                procedure_ids=tuple(agent["procedure_ids"]),
                profile=profile,
                fragments=fragments,
            )
        )

    repository = _posix_relative(instructions_raw["repository"], "instructions.repository")
    path_specific: list[MappingProxyType[str, object]] = []
    for index, entry in enumerate(instructions_raw["path_specific"]):
        apply_to = _posix_relative(
            entry["apply_to"], f"instructions.path_specific[{index}].apply_to"
        )
        instruction = _posix_relative(
            entry["instruction"], f"instructions.path_specific[{index}].instruction"
        )
        path_specific.append(
            MappingProxyType(
                {
                    "apply_to": apply_to.as_posix(),
                    "instruction": instruction.as_posix(),
                }
            )
        )
    return Catalog(
        agents=tuple(agents),
        procedures=tuple(ProcedureSpec(**item) for item in procedures_raw),
        contracts=MappingProxyType(dict(contracts_raw)),
        instructions=InstructionCatalog(repository=repository, path_specific=tuple(path_specific)),
    )
