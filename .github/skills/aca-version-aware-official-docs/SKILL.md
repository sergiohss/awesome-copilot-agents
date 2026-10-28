---
name: aca-version-aware-official-docs
description: Use when implementation guidance must follow installed project versions and local docs before optional official capability.
---

## When to use

Use when implementation guidance must follow installed project versions and local docs before optional official capability.

## Workflow

Prefer repository lockfiles, package metadata, and local docs before optional official documentation.

## Checks

Confirm guidance matches the installed version in the project's lockfile or package manifest, not a generic or latest-version assumption; mark official-documentation capability as unavailable when it cannot be reached.

## Output

Return the version-evidence path and, when used, the official documentation reference inside Handoff v1 without fabricating version-specific behavior.

## References

- None
