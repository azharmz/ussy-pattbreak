# Breakout Contract v2 — shadow specification

Status: **DESIGN FROZEN FOR SHADOW VALIDATION; NOT PRODUCTION-ACTIVE**

This contract closes the identity/lifecycle ambiguity found in the 2026-09-17
production audit without modifying frozen O'Neil morphology (#33).

## Evidence baseline

On 2026-09-17 Core v1 produced 426 assessment-level candidate hits across 25
securities and 58 exact `(security_id, pivot_level)` groups.

A PIT reconstruction using the exact frozen READY object classified the 426 hits
using the existing close-cross rule and the existing 1.40x prior-50-day volume
threshold, with eligibility beginning at each assessment's `structural_end`
(fallback only for diagnostics: pivot_source_date, then structural_start):

- 293 assessment hits: FIRST_QUALIFYING_BREAKOUT
- 133 assessment hits: RECYCLED_PIVOT
- the 293 survivors represented 243 base identities, 117 lineage identities,
  and 48 exact security/pivot groups
- zero surviving base_id groups spanned multiple pivots
- nine lineage_id groups spanned multiple pivots
- 31 surviving pivot groups contained multiple base_ids

Therefore assessment_id is too granular for a trade candidate, lineage_id is too
broad for lifecycle consumption, and security+pivot alone is too coarse for
structure lifecycle.

## v2 identity model

### 1. Morphology observation

`assessment_id` remains immutable provenance for one #33 morphology observation.
It is never the economic trade/event identity.

### 2. Structure lifecycle

`base_id` is the structural identity supplied by frozen #33. Lifecycle
eligibility is scoped to a base observation and starts no earlier than its
`structural_end`.

For a recognized assessment to survive the lifecycle gate, the current bar must
be the **first qualifying breakout on or after that assessment's structural_end**.

A qualifying breakout uses the existing Core v1 completed-bar rules:

```
prior_close <= pivot < close
volume / prior_50_volume_mean >= 1.40
```

If an earlier qualifying breakout exists after that assessment became eligible,
that assessment is `RECYCLED_STRUCTURE_BREAKOUT` and cannot create another
candidate.

This does not impose a maximum base age and does not modify #33 morphology.

### 3. Economic breakout event

After the structure lifecycle gate, surviving assessments are consolidated by:

```
(security_id, signal_date, exact pivot_level)
```

One event preserves all contributing provenance rather than discarding it:

- assessment_ids
- base_ids
- lineage_ids
- pattern families
- structural_start / structural_end
- pivot_source_date
- morphology schema/engine lineage

One economic pivot event must produce at most one downstream T+1 evaluation.

### 4. Competing pivots

Multiple distinct pivot events for the same security and signal_date remain
distinct in v2 shadow output.

v2 does **not** silently select highest/newest/oldest pivot and does not introduce
an arbitrary age rule. Resolving competing pivots is a separate policy contract
that requires evidence. Until that contract exists, shadow output labels these
events as competing when applicable.

### 5. Gap mechanics

Core v1 only consumes prior close, close, and volume. v2 shadow must preserve
that behavior for comparability. It must not silently reinterpret a close-to-close
cross as an intraday cross.

A future OHLC-aware extension may classify `GAP_ABOVE_PIVOT` versus
`INTRADAY_CROSS`; gap eligibility is not changed by this contract.

## Required shadow output

The v2 shadow builder must emit one record per consolidated economic event with
a deterministic event_id and at least:

```
event_id
security_id
signal_date
pivot_level
breakout_volume_ratio
event_state
competing_pivot
assessment_ids[]
base_ids[]
lineage_ids[]
pattern_types[]
structural_ends[]
breakout_version
morphology_schema
morphology_engine
source_candidate_contract
```

Deterministic event identity is a hash of the canonical tuple
`(security_id, signal_date, normalized exact pivot representation)`; it must not
depend on assessment ordering.

## Fail-closed invariants

- exact frozen READY and morphology lineage must verify before reconstruction
- every surviving assessment must carry base_id and structural_end in production
  v2 input; missing structural identity is not silently inferred
- all assessments consolidated into one event must agree on security, signal
  date, exact pivot, and current breakout-volume evidence
- one base_id must not map to conflicting pivot levels within the same frozen
  morphology contract; conflict fails the shadow run
- shadow artifacts are immutable and versioned separately from Core v1
- no v1 current pointer, T+1 checkpoint, lifecycle checkpoint, or dashboard
  projection may be advanced by shadow validation

## Promotion gate

Production promotion is prohibited until shadow recomputation demonstrates:

1. exact reconciliation of the 426 v1 assessment hits
2. lifecycle classification reconciliation (293 first / 133 recycled) against
   the frozen 2026-09-17 audit baseline
3. deterministic consolidation of the lifecycle survivors
4. explicit reporting of competing-pivot securities/events
5. regression tests proving one economic event cannot fan out into multiple T+1
   executions
6. downstream migration plan for candidate_id -> event_id lineage

Only after those checks pass may candidate -> T+1 -> lifecycle be recomputed
under a separately versioned production contract.
