# Dashboard V2 — compact opportunity serving contract

Status: implementation baseline.

## Purpose

Expose current RECOGNIZED O'Neil structures to the dashboard without loading the raw morphology checkpoint at the edge. This is a serving/observability projection only; Core morphology, breakout, T+1 and lifecycle semantics remain unchanged.

## Producer-side flow

```text
verified raw morphology + exact READY
        ↓
compact opportunity snapshot
        ↓
R2 dashboard-opportunities/current.json
        ↓
Worker/D1
```

The compact snapshot contains one current-as-of row per recognized assessment with a pivot and exact current READY close. It preserves `assessment_id`, `base_id`, `lineage_id`, `security_id`, pattern, pivot and structural dates.

Derived presentation fact:

```text
distance_to_pivot_pct = (as_of_close / pivot_level - 1) * 100
```

No `PRE_BREAKOUT` or `NEAR_TRIGGER` Core state is created. Breakout states remain owned by the breakout evaluator and are joined separately by exact `assessment_id == candidate_id` when a confirmed candidate exists.

## Fail-closed lineage

The producer verifies the raw morphology JSONL SHA-256 and records both raw morphology and READY source hashes. The snapshot is immutable/content-addressed when published; a small current pointer selects the serving version.

## Edge constraint

Cloudflare Worker must never parse the raw morphology checkpoint. Only this compact snapshot plus candidates, T1, lifecycle and small universe metadata may be used for dashboard serving.
