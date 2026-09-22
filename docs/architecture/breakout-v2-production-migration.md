# Breakout Contract v2 — production migration plan

Status: **MIGRATION CONTRACT FROZEN; PRODUCTION V1 REMAINS ACTIVE**

## Validated evidence

The shadow contract has reproduced two independent production cohorts:

| signal date | v1 assessment hits | first qualifying | recycled | v2 economic events | competing events | competing securities |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09-17 | 426 | 293 | 133 | 48 | 42 | 16 |
| 2026-09-18 | 458 | 265 | 193 | 50 | 11 | 5 |

The migration therefore changes identity and lifecycle semantics. It is not a
dashboard-only change and must not reuse v1 candidate/T1/lifecycle pointers as
if they were v2 outputs.

## Frozen identity boundaries

1. `assessment_id` — immutable #33 morphology observation provenance.
2. `base_id` — morphology structure lifecycle identity.
3. `event_id` — economic breakout event identity, deterministic from
   `(security_id, signal_date, exact pivot_level)` after the first-qualifying
   lifecycle gate.
4. `position_id` — security-level executed position identity. It must not be
   derived directly from an assessment id.

`lineage_id` remains ancestry/provenance and is not a consumption key.

## Stage contract

### A. Morphology

Frozen #33 is unchanged. Existing immutable morphology checkpoints are reusable
when their READY lineage verifies.

### B. Breakout events v2

Input: verified immutable morphology + exact frozen READY.

Output stage: `breakout-events-v2`.

Required record fields are the v2 shadow event fields plus complete contributing
morphology provenance. Recycled structure breakouts do not emit events.

Immutable object key is content-addressed. A v2 current pointer is separate from
the v1 `candidates/current.json` pointer until cutover.

### C. T+1 event execution v2

Input: immutable `breakout-events-v2` checkpoint + later exact READY.

The existing execution price rule is retained:

- earliest observed session after signal date;
- fill at observed T+1 daily open;
- below pivot => not executed;
- more than 5% above that event's pivot => missed/extended;
- otherwise executable.

The 5% buy-zone rule is an **execution eligibility gate**, not a competing-pivot
selector.

One event may produce at most one T+1 event-execution record. The output carries
`event_id` and the upstream event checkpoint hash. It must not manufacture a
v1 assessment `candidate_id`.

### D. Security-level execution arbitration

Several pivot events for the same security/date can independently be executable
at the same observed T+1 open. They are alternative explanations for one
security order, not multiple positions.

Group executable event records by:

`(security_id, fill_date, fill_price)`

A group creates at most one security execution. All eligible `event_id` values,
pivots and morphology provenance are retained as contributing evidence.

No highest/newest/nearest pivot selector is introduced. If executable rows for
one security disagree on fill date or observed fill price, fail closed.

### E. Position lifecycle v2

A position is opened from one arbitrated security execution, not one assessment
or pivot event.

Deterministic identity:

`position_id = hash(security_id, entry_date, observed_entry_price, execution_contract_version)`

The position preserves `contributing_event_ids[]` and contributing pivots.
Technical exit arbitration remains downstream and must consume the security
position identity.

No max hold is introduced.

### F. Dashboard projection

Dashboard remains a disposable projection. It may expose one signal/event view
and one position view, but must not collapse provenance in R2.

Historical reconstruction comes from immutable R2 v2 checkpoints. D1 remains a
current read model only.

## Durable namespaces

During shadow and migration, v1 and v2 must coexist:

- `pattern-breakout/production/breakout-events-v2/runs/{signal_date}/{hash}.jsonl`
- `pattern-breakout/production/t1-event-execution-v2/runs/{signal_date}/{hash}.jsonl`
- `pattern-breakout/production/security-execution-v2/runs/{signal_date}/{hash}.jsonl`
- `pattern-breakout/production/lifecycle-v2/runs/{as_of_date}/{hash}.jsonl`

Each stage has a separate v2 pointer/index. No v1 pointer is advanced by shadow
runs.

Every manifest must record upstream source identity/hash, READY identity/hash,
producer commit/run, schema/contract version and creation timestamp.

## Fail-closed invariants

- exact upstream hashes verify before every stage;
- one `event_id` cannot fan out into multiple T+1 rows;
- one security execution cannot fan out into multiple OPEN positions;
- multiple event explanations for one observed security fill are preserved, not
  silently discarded;
- conflicting fill dates/prices for the same security arbitration group fail;
- v1 candidate_id is never silently reinterpreted as v2 event_id;
- dashboard cannot become the source of lifecycle truth;
- a semantic or lineage mismatch requires recomputation from the nearest valid
  immutable checkpoint.

## Migration sequence

1. Implement and unit-test the durable `breakout-events-v2` publisher without
   a production cutover.
2. Implement T+1 event execution v2 by adapting the existing entry rule to
   `event_id`.
3. Implement explicit security-level execution arbitration.
4. Implement lifecycle v2 opening from the arbitrated execution and preserve
   contributing event provenance.
5. Run end-to-end shadow recomputation for 2026-09-17 and 2026-09-18.
6. Assert reconciliation against the validated event counts and verify that
   security-level executions/positions do not fan out.
7. Project the v2 shadow lifecycle into a disposable dashboard test projection.
8. Only after all gates pass, perform one atomic production cutover of the
   consumer contract. Keep immutable v1 evidence available for rollback/audit.

## Promotion gates

Production v2 is blocked until all are true:

- 17 Sep: 426 -> 293/133 -> 48 events reproduces exactly.
- 18 Sep: 458 -> 265/193 -> 50 events reproduces exactly.
- deterministic hashes are stable on rerun from identical frozen inputs;
- T+1 event execution has exactly one row per event;
- security arbitration proves at most one execution per security/fill;
- lifecycle proves at most one OPEN position per arbitrated execution;
- no duplicate security position is created solely because several pivots were
  eligible;
- v2 dashboard can be rebuilt from R2 alone;
- v1 production pointers remain untouched until the explicit cutover commit.

## Explicit non-decisions

This migration does **not** add a max pattern age, alter frozen #33, choose the
highest/newest/nearest competing pivot, reinterpret gap breakouts, or change the
technical exit methodology. Those require separate evidence and contracts.
