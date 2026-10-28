---
name: aca-severity-based-code-review
description: Use when reviewing completed changes with evidence-backed severities and PASS or BLOCK disposition.
---

## When to use

Use when reviewing completed changes with evidence-backed severities and PASS or BLOCK disposition.

## Workflow

Grade findings with file:line evidence, severity, disposition, positives, checklist, and PASS or BLOCK.

## Checks

Confirm every finding carries file:line evidence and an explicit severity, and the overall disposition is exactly PASS or BLOCK with no unresolved blocking finding left ungraded.

## Output

Return the graded findings, positives, checklist, and PASS or BLOCK disposition inside `code-review-v1`.

## References

- None
