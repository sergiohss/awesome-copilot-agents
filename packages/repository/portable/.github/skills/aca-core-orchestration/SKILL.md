---
name: aca-core-orchestration
description: Use when coordinating multi-step work across the 33-agent catalog with Route Plan v1, Handoff v1, specialist precedence, and surface fallbacks.
---

## When to use

Use when coordinating multi-step work across the 33-agent catalog with Route Plan v1, Handoff v1, specialist precedence, and surface fallbacks.

## Workflow

Load references/catalog.md and references/contracts.md when routing or returning Route Plan v1.

## Checks

Confirm the recommended `agent_id` exists among the 33 canonical IDs, concurrency groups contain at most two agents, dangling source edges resolve per references/catalog.md, and cloud recommendations use `cloud-separate-session` without claiming delegation already executed.

## Output

Return Route Plan v1 or Handoff v1 with `contract_id` from references/contracts.md, the exact specialist whitelist and exclusions, and approval checkpoint state.

## References

- references/catalog.md
- references/contracts.md
