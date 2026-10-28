---
name: aca-secure-code-assessment
description: Use for read-only security assessment with scope, threats, controls, and remediation disposition.
---

## When to use

Use for read-only security assessment with scope, threats, controls, and remediation disposition.

## Workflow

Stay read-only; load references/severity.md for scope, threats, controls, and remediation disposition.

## Checks

Confirm the assessment stays read-only with no remediation edits applied, and every threat/control finding in references/severity.md has evidence and a severity before disposition.

## Output

Return the scope, assets, threats, severities, evidence, controls, remediation recommendations, and verification disposition inside `python-security-assessment-v1`; remediation is deferred to a separate assignment.

## References

- references/severity.md
