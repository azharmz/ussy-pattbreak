# Dashboard V1

This directory is the read-only serving layer for Pattern Breakout production.

Core facts remain authoritative in R2 durable artifacts. D1 is a rebuildable projection. No dashboard code may alter Core signal, T+1, lifecycle or exit semantics.

## Data model

- projection_runs: projection lineage/freshness
- opportunities: PIT Core observations keyed by assessment_id, retaining base_id and lineage_id
- positions: projected lifecycle state
- events: deterministic lifecycle events only
- opportunity_evidence: optional versioned extension evidence

"Pre-Breakout" is a UI label derived from Core facts (for example RECOGNIZED + PIVOT_NOT_CROSSED plus distance_to_pivot). It is not a Core state.

Extension evidence may attach before breakout and must distinguish NOT_AVAILABLE from NOT_CONFIRMED.

See docs/architecture/dashboard-v1.md and d1/schema.sql.
