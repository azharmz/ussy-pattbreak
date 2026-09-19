# Frozen Morphology Adapter v1

This adapter resolves the production interface mismatch without modifying the
frozen O'Neil engine.

## Immutable morphology dependency

- repository: `azharmz/ussy-oneil-patterns`
- commit: `c433cc1e35a5aa32a46f732cd8c5545935e36e40`
- output schema: `oneil-pattern-output-v2`
- engine: `33-core-p8-frozen-v1`

The frozen repository's historical direct R2 reader expects READY schema v1.
Current `ussy-data` production emits READY schema v2. Pattern Breakout therefore
must not call the frozen repository's `run_from_r2()` wrapper.

Instead:

`FROZEN_READY v2 -> verified exact Parquet bytes -> PIT slice -> frozen
run_ready_dataset() + analyze_security() -> oneil-pattern-output-v2 ->
RAW_ONEIL_MORPHOLOGY`

No detector implementation is copied or altered.

## Checkpoint

The RAW_ONEIL_MORPHOLOGY checkpoint records the exact frozen repository SHA,
engine/output versions, upstream FROZEN_READY identity/hash, record count, and
SHA-256 of deterministic morphology JSONL.

A mismatch in READY bytes, READY schema, morphology output schema, or engine
version fails closed.
