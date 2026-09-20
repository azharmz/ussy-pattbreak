# Extension Evidence Contract v1

## Boundary

Core v1 is frozen and authoritative. Extension engines are independent,
evidence-only enrichments. They MUST NOT change O'Neil morphology acceptance,
breakout eligibility, T+1 execution, position lifecycle, or exits.

The two planned extension families are:

- `WEINSTEIN_V1`: broader stage/trend context.
- `MINERVINI_VCP_V1`: contraction/tightening evidence.

No numerical Weinstein/VCP rule is frozen by this document. Each engine requires
its own source-lock before methodology code is introduced.

## Core facts, not invented states

Frozen O'Neil morphology states remain `RECOGNIZED`, `AMBIGUOUS`, and
`REJECTED`. Breakout evaluation remains separate. The extension layer MUST
NOT invent `NEAR_TRIGGER`, `PIVOT_DEFINED`, or `PRE_BREAKOUT` as Core
states.

A UI may derive a presentation label such as "Pre-Breakout" from recognized
Core facts (for example distance to pivot), but that is a projection.

## Identity and PIT

Evidence attaches to an exact observation using `assessment_id` and preserves
structural continuity with `base_id` and `lineage_id`. `as_of_date` is
mandatory. Extension engines may therefore enrich a recognized base before a
breakout without waiting for `TECHNICAL_BREAKOUT_CANDIDATE`.

## Evidence semantics

`NOT_AVAILABLE` means the extension was not produced and MUST NOT be treated
as false evidence. `NOT_EVALUABLE` means inputs/methodology requirements did
not permit evaluation. Negative evidence uses `NOT_CONFIRMED` or
`NOT_DETECTED` as defined by the eventual source-locked engine.

No composite score and no rule equivalent to
`Core AND Weinstein AND VCP = candidate` belongs in Extension v1.

## Storage target

Production extension checkpoints should live separately from Core lifecycle,
for example:

`pattern-breakout/production/extensions/<extension>/...`

D1/dashboard projections may join evidence to Core opportunities, but R2
remains authoritative and extension failure must not block Core production.
