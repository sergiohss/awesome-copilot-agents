---
name: aca-human-approval-checkpoint
description: Use when orchestrated complex work requires approve, revise, or stop before execution planning.
---

## When to use

Use when orchestrated complex work requires approve, revise, or stop before execution planning.

## Workflow

Present assumptions and planned slices; wait for approve, revise, or stop before execution planning.

## Checks

Confirm the checkpoint state is exactly `pending`, `approved`, `revised`, or `stopped`, and that no slice is assigned or delegated while state is `pending` or `stopped`.

## Output

Return the checkpoint state and any revisions inside Handoff v1's `routing`/`result` fields before execution planning proceeds.

## References

- None
