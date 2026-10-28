---
name: aca-structured-implementation-handoff
description: Use when returning typed Handoff v1 results with artifact paths and next-agent routing.
---

## When to use

Use when returning typed Handoff v1 results with artifact paths and next-agent routing.

## Workflow

Emit Handoff v1 with contract_id, status, artifact_paths, routing, and typed result fields.

## Checks

Confirm `contract_id` matches the profile's one primary contract, `status` is exactly `completed`, `blocked`, or `needs-approval`, and source-required fields stay inside `result` rather than flattened into `summary`.

## Output

Return the Handoff v1 envelope with `handoff_version`, `contract_id`, `status`, `summary`, `artifact_paths`, `routing`, and typed `result` populated.

## References

- None
