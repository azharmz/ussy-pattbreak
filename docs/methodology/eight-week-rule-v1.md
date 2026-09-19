# Eight-Week Hold Exception v1

Status: source-locked causal state; no performance result consulted.

Official IBD rule represented here:

- qualification requires a gain of **more than 20%** from the ideal/proper buy
  point;
- that gain must occur within **three weeks** of a proper breakout;
- a qualifying rapid winner is held for **at least eight weeks**;
- the breakout week counts as **week 1**.

This state is not a generic maximum holding period. A position that never
qualifies does not become an eight-week-rule position merely because eight weeks
pass.

## Causal persistence

The engine stores the first date on which a completed daily bar proves
qualification. Once qualified, that fact persists. Later price decline does not
rewrite history.

Calendar weeks are Monday-anchored for deterministic daily-bar week counting,
with the week containing the breakout date defined as week 1. This is an
explicit machine operationalization of the source's week-count language.

## Exit integration boundary

This module only determines rapid-winner qualification and whether the minimum
eight-week hold period is still active. It does not itself sell a position.

Profit-zone action and arbitration against defensive/technical sell evidence
must be integrated explicitly in a subsequent contract. No generic max-hold is
introduced.
