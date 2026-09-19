# USSY Pattern Breakout

Technical-only swing system built around O'Neil-style proper-base morphology, pivot breakout, causal T+1 Open execution, and technical exits.

## Core v1

```
canonical OHLCV
  -> frozen O'Neil Pattern Engine
  -> proper base + pivot
  -> pivot crossing + breakout-volume confirmation
  -> TECHNICAL_BREAKOUT_CANDIDATE
  -> T+1 Open executability
  -> OPEN position
  -> technical sell evidence
  -> HOLD / TECHNICAL EXIT
```

Core v1 has no fundamental eligibility, no max-hold, no fixed-R target, and no dependency on TrendFoll strategy logic.

Canonical morphology dependency:

- repo: `azharmz/ussy-oneil-patterns`
- frozen SHA: `c433cc1e35a5aa32a46f732cd8c5545935e36e40`
- schema: `oneil-pattern-output-v2`
- engine: `33-core-p8-frozen-v1`
- patterns: `CUP_WITH_HANDLE`, `CUP_WITHOUT_HANDLE`, `DOUBLE_BOTTOM`, `FLAT_BASE`

Weinstein Stage Analysis and Minervini/VCP are future independently versioned evidence extensions, not Core v1 gates.

See `docs/architecture/core-v1.md` and `docs/audits/existing-entry-exit-assets-v1.md`.
