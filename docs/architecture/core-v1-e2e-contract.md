# Core v1 End-to-End Contract

Status: IMPLEMENTATION VALIDATION

The Core v1 engineering path is:

```
frozen O'Neil assessment
 -> completed-bar pivot crossing + breakout volume >= 1.40
 -> TECHNICAL_BREAKOUT_CANDIDATE
 -> causal T+1 Open executability
 -> OPEN
 -> source-locked technical evidence
 -> EXIT_PENDING
 -> causal next-session Open
 -> CLOSED
```

## Invariants

- Morphology remains owned by the frozen O'Neil engine.
- No fundamental/CAN SLIM eligibility is required.
- A valid breakout may be missed at T+1 because the observed open is extended; this does not rewrite signal quality.
- An unconfirmed breakout cannot reach executable entry.
- Entry fill is the observed T+1 Open.
- Exit evidence is evaluated only from completed periods.
- Actionable exit evidence does not receive a same-bar fill; execution is the next observed session open.
- HOLD has no elapsed-time conversion to exit.
- No max-hold, ATR exit, fixed-R target, round-trip automation, climax-top automation, or composite score exists in Core v1.
- Deferred methodology rules remain deferred.

This validation is structural/causal. It is not a performance claim and does not tune frozen morphology or thresholds from returns.
