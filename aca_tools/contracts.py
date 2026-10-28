from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .errors import ValidationError
from .models import Catalog


_SCHEMA_DIR = Path(__file__).resolve().parents[1] / "src/schemas"


def _field_path(parts: list[object]) -> str:
    result = ""
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += ("." if result else "") + str(part)
    return result or "handoff"


def _load_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path.name}: cannot load JSON schema: {error}") from error


@lru_cache(maxsize=1)
def _handoff_validator() -> Draft202012Validator:
    schema = _load_json(_SCHEMA_DIR / "handoff-v1.schema.json")
    return Draft202012Validator(schema)


@lru_cache(maxsize=1)
def _result_contracts() -> dict[str, object]:
    document = _load_json(_SCHEMA_DIR / "result-contracts.schema.json")
    defs = document.get("$defs")
    if not isinstance(defs, dict):
        raise ValidationError("result-contracts.schema.json: missing $defs")
    return defs


def primary_contract_ids() -> frozenset[str]:
    return frozenset(_result_contracts().keys())


def _validate_against(validator: Draft202012Validator, payload: object, *, label: str) -> None:
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        raise ValidationError(f"{label}.{_field_path(list(error.absolute_path))}: {error.message}")


def _validate_route_plan_rules(result: Mapping[str, object]) -> None:
    groups = result.get("concurrency_groups")
    if not isinstance(groups, list):
        raise ValidationError("result.concurrency_groups: must be an array")
    for index, group in enumerate(groups):
        if not isinstance(group, list):
            raise ValidationError(f"result.concurrency_groups[{index}]: must be an array")
        if len(group) > 2:
            raise ValidationError(
                f"result.concurrency_groups[{index}]: must contain at most two agents"
            )
    mode = result.get("surface_execution_mode")
    if mode == "cloud-separate-session":
        if result.get("subagent_executed") is True:
            raise ValidationError(
                "result.subagent_executed: cloud handoffs must not claim subagent execution"
            )
        if result.get("delegation_executed") is True:
            raise ValidationError(
                "result.delegation_executed: cloud handoffs must not claim delegation execution"
            )


def _validate_unavailable_capability(payload: Mapping[str, object]) -> None:
    result = payload.get("result")
    if not isinstance(result, Mapping):
        return
    requires_visual = result.get("requires_visual_capability") is True
    requires_mcp = result.get("requires_mcp_capability") is True
    if not (requires_visual or requires_mcp):
        return
    status = payload.get("status")
    evidence = result.get("unavailable_evidence")
    if status == "blocked":
        return
    if isinstance(evidence, str) and evidence.strip():
        return
    raise ValidationError(
        "result.unavailable_evidence: visual or MCP dependency requires explicit "
        "unavailable evidence or blocked status"
    )


def validate_handoff(
    agent_id: str,
    payload: Mapping[str, object],
    catalog: Catalog,
) -> None:
    """Validate one Handoff v1 payload for the agent's primary contract and routing rules."""
    _validate_against(_handoff_validator(), payload, label="handoff")

    contract_id = payload.get("contract_id")
    if not isinstance(contract_id, str):
        raise ValidationError("handoff.contract_id: must be a string")

    agent = next((item for item in catalog.agents if item.id == agent_id), None)
    if agent is not None and contract_id != agent.contract_id:
        raise ValidationError(
            f"handoff.contract_id: expected {agent.contract_id} for agent {agent_id}"
        )

    defs = _result_contracts()
    if contract_id not in defs:
        raise ValidationError(f"handoff.contract_id: unknown contract {contract_id}")

    try:
        contract_validator = Draft202012Validator(defs[contract_id])
    except SchemaError as error:
        raise ValidationError(f"contract {contract_id}: invalid schema: {error}") from error

    result = payload.get("result")
    _validate_against(contract_validator, result, label="result")

    routing = payload.get("routing")
    if isinstance(routing, Mapping):
        next_agent = routing.get("recommended_next_agent")
        if isinstance(next_agent, str):
            known = {item.id for item in catalog.agents}
            if known and next_agent not in known:
                raise ValidationError(
                    f"routing.recommended_next_agent: unknown agent {next_agent}"
                )

    if contract_id == "route-plan-v1" and isinstance(result, Mapping):
        _validate_route_plan_rules(result)

    _validate_unavailable_capability(payload)
