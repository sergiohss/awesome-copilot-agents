---
name: aca-deployment-safety-pipeline
description: Use when planning CI/CD rollout, rollback, credential, and infrastructure gates under AP-X.
---

## When to use

Use when planning CI/CD rollout, rollback, credential, and infrastructure gates under AP-X.

## Workflow

Load references/rollout-rollback.md for staged rollout, rollback triggers, and credential gates.

## Checks

Confirm references/rollout-rollback.md staged rollout and rollback triggers are defined before any pipeline or infrastructure change, and credential-bearing steps carry explicit AP-X approval.

## Output

Return the pipeline/deployment artifact with rollout stages, rollback triggers, and credential/infrastructure gate status inside Handoff v1.

## References

- references/rollout-rollback.md
