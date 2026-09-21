# Audit — Exit dependency on pivot identity

Status: diagnostic architecture audit. No production semantics changed.

## Finding

The current position field `pivot_level` is passed into
`PositionTechnicalContext.proper_buy_point`. It is therefore not merely
provenance. Two active exit mechanisms depend numerically on the selected pivot:

1. Normal profit zone: `proper_buy_point * 1.20` (the implementation records a
   1.25 ceiling but becomes actionable once close reaches the 1.20 floor).
2. Eight-week rapid-winner qualification: high must exceed
   `proper_buy_point * 1.20` during the first three breakout weeks.

The defensive-loss rule is independent of pivot and uses purchase price * 0.93.
The weekly 10-week moving-average violation is also independent of pivot.

## Consequence for v2

A security-level position supported by multiple executed pivot-events cannot
inherit an arbitrary single pivot without changing profit-taking and eight-week
qualification behavior.

The following shortcuts are therefore prohibited until source/methodology
evidence defines them:

- lowest supporting pivot
- highest supporting pivot
- newest/oldest pivot
- average pivot
- whichever assessment happened to be processed first

## Required separation

v2 should distinguish:

- morphology evidence identity (assessment/base/lineage)
- breakout event identity (security, signal date, pivot)
- economic execution identity (security, T+1 session/fill)
- position identity (one economic holding)
- **exit reference contract** (the proper buy point governing profit-zone and
  eight-week calculations)

Supporting pivots remain provenance unless/until an explicit exit-reference
arbitration selects a proper buy point.

## Current dependency matrix

| Rule | Uses purchase price | Uses proper buy point/pivot | Independent market level |
| --- | --- | --- | --- |
| 7% defensive loss | yes | no | no |
| 20–25% normal profit zone | no | yes | no |
| rapid-winner / eight-week exception | no | yes | no |
| weekly 10-week MA violation | no | no | yes |

This means security-level execution deduplication is safe for fill identity, but
position migration is not complete until the exit-reference contract is frozen.
