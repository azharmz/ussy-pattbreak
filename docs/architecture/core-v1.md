# Pattern Breakout Core v1

Status: DESIGN FROZEN FOR CORE IMPLEMENTATION

## Decisions

1. Technical-only: no C/A/N/I or fundamental eligibility.
2. Fundamental failure never removes a technical candidate.
3. Frozen O'Neil Pattern Engine is the morphology authority.
4. Core path is Pattern -> Pivot -> Breakout + volume -> Technical Candidate -> T+1 Open -> Position -> Technical Exit.
5. No max-hold and no forced time exit.
6. No fixed 2R target or ATR exit inherited from older USSY research.
7. Holding period is an outcome, not an exit rule.
8. Signal uses completed daily bar T; earliest USSY execution is T+1 Open.
9. A valid breakout remains a valid signal even if T+1 is missed/extended.
10. TrendFoll is not a methodology dependency.
11. Weinstein and Minervini/VCP are outside Core v1 and begin as evidence-only extensions.
12. No composite score in Core v1.
13. No Wyckoff, Darvas, MACD, RSI, stochastic, Bollinger, or unrelated indicators in Core v1.
14. Rule provenance must distinguish ORIGINAL, OPERATIONALIZATION, DATA_ADAPTATION, PROXY, ENGINEERING, UNAVAILABLE.

## Recovery boundaries

Before heavy full-universe compute:

```
prepare
 -> frozen READY identity
 -> raw O'Neil morphology checkpoint
 -> breakout candidate checkpoint
 -> T+1 execution checkpoint
 -> lifecycle checkpoint
 -> validate/report
```

Durable checkpoints must carry source identity/hash, schema/version, contract/config identity, producer commit/run and created_at. Resume fails closed on lineage mismatch.

## Separation

CAN SLIM v1 remains a frozen historical baseline. CAN SLIM v2 remains fundamental-first. Pattern Breakout is an independent technical product and must use its own namespaces and contracts.
