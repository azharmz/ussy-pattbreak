# Opportunity Serving Contract v1

Status: **frozen serving boundary; no opportunity eligibility policy exists.**

## Meaning and identity

An assessment is morphology evidence, not an Opportunity. `assessment_id` is a
point-in-time morphology observation. `base_id` is the frozen structural
lifecycle identity, and `lineage_id` is conservative ancestry across structural
evolution. A breakout event is the separate economic identity
`(security_id, signal_date, exact pivot_level)`. T+1 execution and a position
are downstream economic records; none may be inferred from an assessment.

The 2026-09-21 dashboard-opportunities snapshot contains **56,441 assessment
evidence rows**. Its only safe serving cardinality is therefore 56,441 R2
records, keyed by `assessment_id`. It must not be deduplicated by security,
base, lineage, or pivot: each changes what the record means. Exact
base/lineage/pivot group counts are audit outputs from the immutable snapshot,
not serving keys and not an eligibility rule.

## Storage and write budget

R2 stores the immutable 56,441-row evidence snapshot and its small metadata
and current-pointer objects. D1 stores **zero** `current_opportunities` rows
until a separately approved opportunity eligibility contract exists. A current
projection therefore has zero opportunity-row writes after the one-time purge
and only writes the small breakout-event and position projections. This avoids
the prior 56,441-row D1 write/storage amplification on every refresh.

`opportunity_candidates_r2` is an observability count only, not an Opportunity
count, and D1 remains disposable and rebuildable from R2.

## Prohibited inference

No serving code may create an Opportunity from a below-pivot observation, a
distance-to-pivot value, a pattern family, a base age, or a T+1 entry-zone.
Those facts are evidence or downstream execution facts. The frozen O'Neil
morphology, breakout confirmation, pivot rules, T+1 entry-zone, and lifecycle
methodology are unchanged by this contract.
