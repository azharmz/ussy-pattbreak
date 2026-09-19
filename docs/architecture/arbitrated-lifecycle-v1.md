# Arbitrated Lifecycle v1

The lifecycle now has an explicit boundary between **evidence arbitration** and
**execution**.

Only `ACTION_EXIT` may move an OPEN position to `EXIT_PENDING`. HOLD and an
active eight-week profit-taking block leave the position OPEN.
`NOT_EVALUABLE` fails closed.

An actionable arbitration verdict records the selected evidence date and reason.
Execution remains causal: the earliest fill is the next observed session open,
never the evidence bar itself.

Identity checks require the selected evidence to belong to the same position and
security. No max-hold or implicit time exit is introduced.

The older `apply_exit_evidence` remains available for its original low-level
contract, but Core integration should route source-locked exits through
`arbitrate_exit -> apply_exit_arbitration -> execute_pending_exit`.
