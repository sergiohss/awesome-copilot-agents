---
name: aca-reproducible-ml-lifecycle
description: Use when designing reproducible data, training, evaluation, and serving metadata for ML work.
---

## When to use

Use when designing reproducible data, training, evaluation, and serving metadata for ML work.

## Workflow

Record dataset hashes, feature schema, training config, evaluation metrics, and serving metadata.

## Checks

Confirm dataset hashes, feature schema, training config, and serving metadata are recorded so the run is reproducible from the artifact alone, not from memory or untracked notebook state.

## Output

Return the dataset/model/training/evaluation/serving metadata inside `ml-data-implementation-v1`'s typed `result`.

## References

- None
