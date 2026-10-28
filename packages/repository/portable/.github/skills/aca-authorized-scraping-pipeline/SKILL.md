---
name: aca-authorized-scraping-pipeline
description: Use only after explicit authorization for acquisition with API preference and compliance controls; never bypass protections.
---

## When to use

Use only after explicit authorization for acquisition with API preference and compliance controls; never bypass protections.

## Workflow

Require authorization first; load references/safety.md for API preference, robots, terms, and rate controls.

## Checks

Confirm explicit authorization exists before any acquisition, an API is preferred over scraping when available, and references/safety.md robots/terms/rate controls are honored with no evasion technique used.

## Output

Return the authorization evidence, source/API preference, compliance controls, schema, validation, and lineage inside `python-acquisition-report-v1`.

## References

- references/safety.md
