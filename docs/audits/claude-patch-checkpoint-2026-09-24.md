# Claude Patch Checkpoint — 2026-09-24

## Status

**APPLIED ON `codex/opportunity-contract-final` AFTER CODEX REVIEW.** This
checkpoint records the patch supplied by the user as `D:/Download/claudeupdate.zip`.
Codex verified that the supplied change resolves the v16/v18 version split and
uses lifecycle, rather than the independent event pointer, as the position
cohort date.

## Supplied files

| ZIP entry | Intended repository path | SHA-256 |
|---|---|---|
| `runtime.js` | `web/d1/runtime.js` | `032447a17daf1d6453fc5e4216f866a099d688e83ed585fc2c41644d915b364a` |
| `compact.js` | `web/d1/compact.js` | `a38dd984df72962bd2d271c8cdfeb39349b52223331ae32dc1538b2fe2776a57` |
| `public.runtime.js` | `web/public/d1/runtime.js` | `032447a17daf1d6453fc5e4216f866a099d688e83ed585fc2c41644d915b364a` |
| `public.compact.js` | `web/public/d1/compact.js` | `a38dd984df72962bd2d271c8cdfeb39349b52223331ae32dc1538b2fe2776a57` |

## Claimed intent

1. Validate execution and lifecycle as one position cohort without requiring
   the independent event pointer to have the same date.
2. Make projection `VERSION` a single source of truth shared by runtime and
   compact projection code.
3. Restore `validCurrent()` readiness and idempotent projection behavior.

## Required review before applying

- Diff each supplied file against current `origin/main`.
- Run the focused JS integration suite and repository Python suite when their
  runtimes are available.
- Verify source and `web/public` mirrors remain identical.
- Check `/api/health` and active D1 generation after deployment.
- Do not infer that an older lifecycle date is a code bug: event and position
  cohorts are intentionally allowed to differ until T+1 is available.
