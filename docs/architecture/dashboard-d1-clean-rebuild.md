# Dashboard D1 clean rebuild contract

Status: **DESIGN FROZEN; destructive reset prepared, not auto-scheduled**

## Boundary

R2 remains the immutable source of truth and is not deleted by this reset. D1 is a disposable current read model and must be rebuildable from verified R2 checkpoints.

## Clean D1 model

- `projection_state`: one current generation/lineage manifest.
- `current_opportunities`: current actionable near-pivot structures only. This table must not be populated by merely renaming breakout events.
- `current_breakout_events`: fresh first-qualifying v2 breakout events.
- `current_positions`: security-level economic positions.

Historical reads remain R2-backed.

## Semantic invariant

Pattern structure != opportunity != breakout event != execution != position.

A recognized morphology record is not automatically an opportunity. Opportunity eligibility needs a separately frozen near-pivot contract. Until that contract is implemented, the clean rebuild must leave `current_opportunities` empty rather than infer a threshold.

## Reset scope

The reset migration drops both legacy normalized dashboard tables and the compact `dashboard_*_v8` serving tables, then creates only the clean read-model tables above.

It never deletes:
- morphology checkpoints;
- breakout-events-v2;
- t1-event-execution-v2;
- security-execution-v2;
- lifecycle-v2;
- READY OHLCV;
- immutable R2 history.

## Safety

Reset is manual-only. The workflow requires the exact confirmation token `RESET_D1`. After reset it verifies the four expected tables exist and legacy dashboard tables do not.

Runtime cutover to the new schema is a separate step. Do not run the destructive reset until runtime/projector support for the clean schema is committed and validated.
