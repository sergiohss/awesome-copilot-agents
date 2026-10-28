---
name: aca-performance-optimization-lifecycle
description: Use when baselining, profiling, changing, comparing, and guarding performance regressions.
---

## When to use

Use when baselining, profiling, changing, comparing, and guarding performance regressions.

## Workflow

Baseline, profile, implement one change, compare deltas, and record regression disposition.

## Checks

Confirm a measured baseline exists before any change, exactly one change is applied per iteration, and the comparison records a regression or improvement disposition rather than an unmeasured guess.

## Output

Return the baseline, profiled bottleneck, applied change, before/after delta, and regression disposition inside Handoff v1's typed `result`.

## References

- None
