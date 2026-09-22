# Opportunity serving contract audit — 2026-09-21

Status: **DECISION RECORDED; D1 OPPORTUNITIES REMAIN EMPTY**

## Identity findings

The repository's existing contracts consistently assign these meanings:

- `assessment_id`: one immutable PIT morphology observation; evidence only.
- `base_id`: exact structure/setup lifecycle identity.
- `lineage_id`: ancestry across structural evolution; never a consumption key.
- `(security_id, signal_date, exact pivot_level)`: economic breakout event.
- execution: T+1 evaluation/fill derived from an event.
- position: security-level holding derived from an execution.

Security, pattern and pivot describe a setup, but do not replace `base_id`.
Pattern and pivot are attributes of a structure; ticker is presentation data and
`security_id` is the durable security identity.

## Production observation

The verified serving health record after the 2026-09-21 snapshot reported:

- 56,441 RECOGNIZED assessment rows below their pivots in canonical R2;
- 0 rows in D1 `current_opportunities`;
- 35 economic breakout events for signal date 2026-09-21;
- 30 current positions in the then-current projection.

The 56,441 figure is assessment cardinality after a factual `close < pivot`
comparison. It is not Opportunity cardinality. Calling those rows Opportunities
would repeat the purged assessment-to-D1 incident.

## Contract decision

Existing semantics are sufficient to audit and compact evidence by `base_id`,
but they are not sufficient to create canonical actionable Opportunities.
Neither `close < pivot` nor grouping by base supplies an eligibility rule.
The frozen repository contract says actionable Opportunity eligibility needs a
separately approved near-pivot contract. No such threshold exists, and the T+1
entry-zone convention applies after breakout, not before it.

Therefore:

1. R2 remains canonical for assessment/setup evidence.
2. D1 `current_opportunities` remains intentionally empty.
3. D1 may continue serving small event and position projections.
4. A future Opportunity implementation requires an explicit user-approved
   eligibility contract and production cardinality audit before any D1 write.

## Repeatable cardinality audit

Run the read-only auditor against the immutable compact snapshot:

```bash
python scripts/audit_opportunity_contract.py \
  checkpoints/dashboard-opportunities.jsonl \
  --expected-as-of 2026-09-21 \
  --output checkpoints/opportunity-contract-audit.json
```

It reports assessment, base/setup, lineage, security-pattern-pivot and
event-shaped group cardinalities; identity conflicts; logical payload bytes;
and full-refresh row amplification. `event_shaped_groups_not_events` is named
deliberately: grouping assessment evidence into an event-shaped tuple cannot
manufacture a breakout event.

D1 byte size is not estimated with a fabricated constant because SQLite/D1
storage depends on pages, JSON size and indexes. The audit instead supplies the
safe planning inputs: exact projected row count, exact logical JSON bytes and
write amplification. Actual D1 storage must be measured on a disposable local
database before promotion.
