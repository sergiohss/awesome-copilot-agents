---
name: aca-orm-query-optimization
description: Use when measuring ORM query, schema, index, and migration risk with before-and-after evidence.
---

## When to use

Use when measuring ORM query, schema, index, and migration risk with before-and-after evidence.

## Workflow

Capture baseline queries, explain plans or ORM metrics, proposed change, and migration risk in references/evidence.md.

## Checks

Confirm references/evidence.md captures the before query/explain-plan evidence, the after evidence post-change, and the migration risk for any schema change.

## Output

Return the before-and-after metrics, schema/index changes, and migration risk disposition inside Handoff v1's typed `result`.

## References

- references/evidence.md
