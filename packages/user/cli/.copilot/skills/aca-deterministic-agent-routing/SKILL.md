---
name: aca-deterministic-agent-routing
description: Use when applying exact canonical agent IDs, exclusions, precedence, and dependencies.
---

## When to use

Use when applying exact canonical agent IDs, exclusions, precedence, and dependencies.

## Workflow

Load references/precedence.md for exact IDs, exclusions, dangling-edge substitutions, and two-agent concurrency limits.

## Checks

Confirm the selected ID is one of the 33 canonical agents, specialists are preferred over universal fallbacks, excluded alternatives are named, and dangling source edges are substituted per references/precedence.md.

## Output

Return the routing decision with `recommended_next_agent`, exclusions, and dependency order inside Handoff v1's `routing` fields.

## References

- references/precedence.md
