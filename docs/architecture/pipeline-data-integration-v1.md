# Pipeline / Data Integration Contract v1

Status: PRE-COMPUTE CONTRACT

Core v1 logic is structurally validated. The next phase integrates real canonical data without turning the first full-universe run into a monolithic workflow.

## Recovery path

```
prepare
 -> FROZEN_READY
 -> RAW_ONEIL_MORPHOLOGY
 -> BREAKOUT_CANDIDATE
 -> T1_EXECUTION
 -> LIFECYCLE
 -> validate/report
```

Every expensive stage writes a durable checkpoint. Runner-local filesystem is not a recovery boundary.

## Required lineage

Each checkpoint must prove:

- source identity (for example the exact READY pointer/object identity);
- source content hash;
- schema version;
- pipeline/contract version;
- producer commit;
- producer run;
- timezone-aware `created_at`.

Resume validates exact lineage and fails closed on mismatch or incomplete metadata.

## Recompute policy

Downstream reporting/metrics changes may reuse a valid checkpoint.

Recompute the applicable upstream stage when semantics change, including morphology engine/schema, breakout definition, T+1 entry semantics, technical exit rules, lifecycle arbitration, PIT/as-of behavior, universe, price basis, corporate-action handling, or source data identity.

## Repository boundaries

Pattern Breakout implementation and pipeline code live in `azharmz/ussy-pattern-breakout`.

The frozen morphology dependency remains `azharmz/ussy-oneil-patterns`. Earlier Pattern Breakout staging in `azharmz/ussy-canslim-research` is reference-only and is not a compute or deployment source.

## Next integration step

Before any heavy run, implement a small adapter that resolves and freezes the canonical `ussy-data` READY identity, validates its hash/metadata, and emits the `FROZEN_READY` checkpoint. Do not run morphology over the full universe until that checkpoint is durable and resumable.
