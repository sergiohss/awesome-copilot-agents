---
name: aca-stack-detection-with-confidence
description: Use when detecting stack, architecture, and confidence with explicit unknowns before routing.
---

## When to use

Use when detecting stack, architecture, and confidence with explicit unknowns before routing.

## Workflow

Report stack signals, architecture shape, confidence, contradictions, and unknowns.

## Checks

Confirm stack claims cite the manifest or lockfile that produced them, confidence is stated per claim rather than as a blanket score, and every contradiction or unknown is listed instead of silently resolved.

## Output

Return `stack-analysis-v1` with detected stack, architecture shape, per-claim confidence, contradictions, unknowns, and specialist recommendations inside Handoff v1.

## References

- None
