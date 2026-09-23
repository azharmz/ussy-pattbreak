# Patch Provenance Checkpoint — 2026-09-24

This checkpoint is a collaboration aid. It records the repository state known
at the time it was written; Git author metadata alone does **not** identify
whether a change was made by Codex, ChatGPT, Claude, or a human.

## Baseline

- Repository `main` at checkpoint: `8c22577`
- Purpose: prevent later work from accidentally treating an earlier assistant
  patch as an unreviewed local change.

## Codex work incorporated before this checkpoint

- `5cfe2a4` — disclose cohort freshness and compact current rows
- `8bfa187` — separate current breakout events from lifecycle
- `34035d2` — advance breakout events before T+1 lifecycle
- `22393a1` — project pattern types into events and positions
- Merge checkpoints: `a120f85` (PR #87), `a9fe15f` (PR #88)

Primary files involved:

- `web/_worker.js`, `web/public/_worker.js`
- `web/d1/runtime.js`, `web/public/d1/runtime.js`
- `web/d1/compact.js`, `web/public/d1/compact.js`
- `web/public/app.js`, `web/public/app.css`
- `web/tests/local-integration.test.mjs`
- `.github/workflows/production-v2-daily.yml`
- `scripts/promote_dashboard_events_current.py`

## Later commits requiring provenance review

These arrived after PR #88 and must be treated as repository state to inspect,
not automatically attributed to a particular assistant:

- `10ee594` — projection invalidation for Pattern labels
- `a1994c2` — position Pattern resolution across event cohorts
- `0a2fea1`, `6cc6aa0`, `7a815ef` — deploy-artifact synchronization
- `de9fa52` — mixed-cohort Pattern lineage test
- `a3e5966` through `8c22577` — isolated acceptance-dispatch markers

Files affected by that later sequence:

- `web/d1/compact.js`, `web/public/d1/compact.js`
- `web/tests/local-integration.test.mjs`
- `.github/workflows/production-v2-daily.yml`
- `.github/dispatch/pattern-projection-v17`
- `.github/dispatch/pattern-projection-v18`

## Rules for the next patch

1. Start from a freshly fetched `origin/main` and read this checkpoint.
2. Before editing an overlapping file, inspect commits after this checkpoint.
3. Preserve frozen O'Neil, pivot, breakout, T+1, and Opportunity contracts.
4. Update this checkpoint in the same PR whenever external assistant or human
   work lands between collaboration turns.
