# AGENTS.md

## Scope

This file governs Codex/engineering work in `azharmz/ussy-pattern-breakout`.

Global engineering governance is maintained in `azharmz/ussy-governance`. Apply its execution, GitHub Actions, compute-heavy workflow, observability, and R2/storage rules together with this repository's local contracts. If global governance is not present in the working tree, do not spend tokens repeatedly searching for it; use this file plus the repository's own authoritative documentation.

## Efficient operating mode

Default to one bounded cycle:

`targeted inspect → brief plan → complete implementation → smallest relevant verification → diagnose/fix → rerun → concise final report`

- Inspect only task-relevant files, failing logs/tests, changed paths, and direct dependencies.
- Do not scan or summarize the whole repository by default.
- Do not repeatedly reread unchanged files or narrate routine steps.
- Prefer targeted search, narrow diffs, and one meaningful patch.
- Avoid unrelated refactors, formatting churn, and speculative cleanup.
- Once scope is clear, continue through ordinary implementation/test/fix steps without asking for repeated approval.
- Run the smallest relevant tests first; broaden only when risk or failures justify it.
- Final report: what changed, verification result, and any real remaining blocker/risk.

## Production / resource guardrail

Before database-, storage-, compute-, or production-heavy changes, explicitly inspect:

1. expected cardinality;
2. read/write amplification;
3. storage/compute impact and blast radius;
4. recovery/checkpoint boundary;
5. whether valid durable evidence/checkpoints can be reused.

Catch design errors with inspection, fixtures, and tests before production. Do not use production reruns as the primary design-debugging loop.

For expensive stages, preserve durable fail-closed lineage and prefer:

`prepare → frozen input checkpoint → heavy compute → durable result checkpoint → validate → publish`

Do not recompute valid expensive outputs for downstream-only reporting, UI, metrics, or logging changes.

## Repository boundaries

This is the **pattern-only technical breakout** project. Keep it separate from CAN SLIM/fundamental screening.

Preserve repository-authoritative frozen contracts. In particular, do not silently change:

- the frozen O'Neil core pattern engine/families;
- pivot methodology;
- breakout volume confirmation threshold;
- first-qualifying-breakout semantics;
- T+1 open execution convention;
- T+1 entry-zone convention;
- lifecycle/exit methodology;
- canonical R2 artifacts, identity, or lineage semantics.

A methodology/threshold/frozen-contract change is a user decision boundary, not an implementation shortcut.

## Storage / serving invariant

- R2 is canonical immutable/durable truth.
- D1 is a disposable, query-oriented serving projection and must be rebuildable from R2.
- A current pointer/generation is not historical truth.
- Do not materialize high-cardinality evidence/assessment datasets into D1 merely because they are available in R2.
- Before adding a D1 projection, estimate row cardinality and write amplification.
- Keep opportunity/setup evidence distinct from breakout events, executions, and positions.
- Do not invent an Opportunity/near-pivot threshold or conflate it with the post-breakout T+1 entry zone.

## Stop conditions

Continue until DONE or genuinely blocked. Stop for a user decision when work would change frozen semantics/methodology, introduce an unapproved threshold, materially change architecture/scope, require unavailable credentials, or perform an unauthorized irreversible/destructive action.

Never label work PASS merely because code was committed. PASS requires the relevant verification evidence.
