# Pattern Breakout Dashboard V1

Status: implementation baseline

## Boundary

Dashboard V1 is a read-only observability and decision-support layer. It never recomputes or mutates Core trading decisions.

Authoritative data remains durable production artifacts in R2. D1 is a disposable query projection and may be rebuilt from durable artifacts.

Core v1 remains frozen. Dashboard labels such as "Pre-Breakout" are presentation categories, not Core methodology states.

## Core facts

Frozen morphology emits normalized status RECOGNIZED, AMBIGUOUS, or REJECTED. Recognized observations may carry base_id, lineage_id, pivot_level and structural fields.

Breakout evaluation remains authoritative for PIVOT_NOT_CROSSED, VOLUME_NOT_CONFIRMED and TECHNICAL_BREAKOUT_CANDIDATE.

For a recognized observation with a pivot, the projection may derive distance_to_pivot from the as-of close. It must preserve the underlying Core facts. No NEAR_TRIGGER or PRE_BREAKOUT Core state is introduced.

## Identity

assessment_id identifies one PIT observation. base_id identifies an exact canonical structure. lineage_id provides conservative continuity across structural evolution.

Dashboard opportunity history preserves all three identities when available.

## Extension evidence

Extensions are optional evidence only. They have no veto over Core opportunities, T+1 execution, positions or exits.

The schema must not add fixed Weinstein/VCP columns to Core opportunity rows. Evidence is attached separately and can exist for recognized/pre-breakout observations before breakout.

Absence of extension output is NOT_AVAILABLE, not NOT_CONFIRMED.

## Serving architecture

R2 durable Core artifacts -> deterministic projection -> D1 -> Worker/API -> Pages.

D1 and the dashboard are disposable serving layers. Failure or staleness in these layers must not affect Core production.

## Durability

GitHub Actions artifacts with 30-day retention remain useful for run inspection/debugging, but are not a durable dashboard source. Morphology, candidate and T+1 outputs required for reconstruction must gain durable R2 checkpoints using immutable run keys plus verified current pointers, following the lifecycle store pattern.

## V1 pages

Overview: health, current counts, latest opportunities, positions needing attention.
Opportunities: recognized/pre-breakout observations and confirmed breakouts/T+1 outcomes.
Positions: OPEN and EXIT_PENDING with Core lifecycle detail.
History: CLOSED positions and descriptive production statistics.

Extension Evidence is an optional section in opportunity/position detail; it is not a required menu or filter.
