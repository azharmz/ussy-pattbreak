# Exit Reference Contract v2 — research decision

Status: DESIGN FROZEN FOR SHADOW VALIDATION; NOT PRODUCTION-ACTIVE.

## Evidence boundary

IBD defines the proper buy point from the active chart structure. For a
base-on-base, the buy point is derived from the second/later base. IBD/MarketSurge
also presents each recognized base with its own optimal buy point, buy zone, and
profit/loss zones. This supports treating a proper buy point as a property of a
specific breakout setup/event, not as an arbitrary security-level aggregate.

This does **not** establish a universal rule that the numerically highest,
newest, lowest, or closest pivot wins when our frozen morphology engine emits
several simultaneous structural hypotheses.

## v2 decision

1. One security may have multiple valid breakout events.
2. T+1 evaluates each event against its own proper buy point and 5% buy zone.
3. If one or more events execute at the same security/session/open, they collapse
   into one economic execution and one position.
4. The position retains all executed supporting event IDs and their proper buy
   points.
5. There is no invented single position-level proper buy point while multiple
   executed events remain unresolved.
6. Pivot-dependent exit rules (20–25% normal profit zone and rapid-winner
   eight-week qualification) must be evaluated per supporting event.
7. Pivot-independent exits (purchase-price defensive loss and weekly 10-week-MA
   violation) are evaluated once at position level.
8. If per-event pivot-dependent exit evidence disagrees, v2 fails closed until
   explicit source-backed arbitration exists. It must not select highest,
   lowest, newest, oldest, average, closest, or first-processed pivot.
9. If all surviving per-event pivot-dependent evidence agrees, that unanimous
   evidence may feed position-level exit arbitration.
10. Provenance must preserve assessment IDs, base IDs, lineage IDs, pattern
    families, event IDs, pivot levels, signal dates, T+1 fill, and source hashes.

## Identity

- assessment_id: morphology observation provenance
- base_id: structural lifecycle identity
- event_id: one breakout event at one pivot
- execution_id: one security + execution session/fill
- position_id: one economic holding
- proper_buy_point: event-level exit reference, not position identity

## Why this contract

The frozen 2026-09-17 audit showed multiple executed pivot-events for the same
security share the exact same T+1 fill. Collapsing fills is therefore an identity
correction. Selecting one of their pivots would instead change profit-zone and
eight-week exit behavior. Event-scoped exit evaluation preserves methodology
without inventing a pivot selector.

## Promotion gate

Before production activation:
- shadow-replay all multi-pivot executions;
- quantify dates where event-level profit/eight-week evidence agrees vs conflicts;
- verify pivot-independent exits are invariant after execution collapse;
- define deterministic fail-closed representation for conflicts;
- recompute candidate/event -> T1 -> lifecycle under immutable lineage.
