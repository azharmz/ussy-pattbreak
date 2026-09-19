# Existing Entry/Exit Asset Audit v1

Source audit: `azharmz/ussy-canslim-research`.

| Existing asset | Decision |
|---|---|
| frozen `ussy-oneil-patterns` engine | REUSE unchanged |
| `execution_entry_v1.py` | EXTRACT causal T+1 mechanics; remove CAN SLIM stage coupling |
| `execution_entry_v2.py` | DO NOT REUSE directly; CAN SLIM v2 adapter |
| `sell_risk_v1.py` | PARTIAL reuse only after rule provenance/source lock |
| `technical_deterioration_v1.py` | evidence reuse candidate |
| `technical_deterioration_action_v1.py` | partial reuse after source lock |
| `round_trip_action_v1.py` | DEFER pending direct source support for exact threshold/action |
| `position_lifecycle_v2.py` | reuse arbitration pattern, not CAN SLIM identity |
| production publishers | engineering reference only; do not reuse CAN SLIM namespace |
| TrendFoll strategy logic | REJECT as methodology source |

## Entry findings

Existing machinery already models causal next-session open, structural pivot, 5% buy-zone ceiling, missed-extended state, below-pivot state, and observed-open fill. Pattern Breakout gets an independent contract accepting only `TECHNICAL_BREAKOUT_CANDIDATE`; it must not masquerade as `CANSLIM_ELIGIBLE`.

Production publisher engineering lessons worth retaining later: immutable source lineage, exact READY hash validation, publication-timeliness guard, no retroactive fill, and separate later observation READY.

## Exit findings

Existing O'Neil/CAN SLIM work contains potentially reusable technical evidence: defensive loss handling, 20-25% profit-zone evidence, eight-week exception evidence, weekly 10-week-MA deterioration, and fail-closed exit arbitration.

It is not a complete drop-in Pattern Breakout exit engine. Climax/abnormal-action channels and the exact round-trip action remain deferred unless directly source-locked.

## Implementation rule

Reuse infrastructure and verified semantics, not CAN SLIM eligibility identity and not TrendFoll decision logic.
