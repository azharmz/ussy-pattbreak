"""Bridge source-locked exit arbitration into the causal position lifecycle."""
from __future__ import annotations

from .exit_arbitration_v1 import ArbitrationState, ExitArbitration
from .lifecycle_v1 import PatternBreakoutPosition, PositionState


def apply_exit_arbitration(
    position: PatternBreakoutPosition,
    arbitration: ExitArbitration,
) -> PatternBreakoutPosition:
    """Schedule next-open execution only from an explicit ACTION_EXIT verdict."""
    if position.state != PositionState.OPEN:
        return position

    if arbitration.state == ArbitrationState.NOT_EVALUABLE:
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})

    if arbitration.state != ArbitrationState.ACTION_EXIT:
        return position

    selected = arbitration.selected
    if selected is None or position.entry_date is None:
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})
    if selected.position_id != position.position_id:
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})
    if selected.security_id != position.security_id:
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})
    if selected.evidence_date < position.entry_date:
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})

    return PatternBreakoutPosition(
        **{**position.__dict__,
           "state": PositionState.EXIT_PENDING,
           "exit_signal_date": selected.evidence_date,
           "exit_reason": selected.state.value})
