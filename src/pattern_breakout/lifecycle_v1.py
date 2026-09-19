"""Pattern Breakout Core v1 independent position lifecycle.

Execution is causal: completed-bar/weekly technical evidence at T schedules the
earliest possible exit at the next observed session open. No time-based exit.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Sequence

from .entry_v1 import EntryState, PatternBreakoutEntry
from .exit_v1 import TechnicalExitEvidence, TechnicalExitState

LIFECYCLE_VERSION = "pattern-breakout-lifecycle-v1"


class PositionState(str, Enum):
    OPEN = "OPEN"
    EXIT_PENDING = "EXIT_PENDING"
    CLOSED = "CLOSED"
    NOT_OPENED = "NOT_OPENED"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class PatternBreakoutPosition:
    position_id: str
    candidate_id: str
    security_id: str
    entry_date: Optional[date]
    entry_price: Optional[float]
    pivot_level: Optional[float]
    state: PositionState
    exit_signal_date: Optional[date] = None
    exit_reason: Optional[str] = None
    exit_date: Optional[date] = None
    exit_price: Optional[float] = None
    lifecycle_version: str = LIFECYCLE_VERSION


def open_from_entry(entry: PatternBreakoutEntry) -> PatternBreakoutPosition:
    if entry.entry_state != EntryState.EXECUTED_T1_OPEN:
        return PatternBreakoutPosition(
            position_id=f"position:{entry.candidate_id}",
            candidate_id=entry.candidate_id, security_id=entry.security_id,
            entry_date=None, entry_price=None, pivot_level=entry.pivot_level,
            state=PositionState.NOT_OPENED)
    return PatternBreakoutPosition(
        position_id=f"position:{entry.candidate_id}",
        candidate_id=entry.candidate_id, security_id=entry.security_id,
        entry_date=entry.fill_date, entry_price=entry.fill_price,
        pivot_level=entry.pivot_level, state=PositionState.OPEN)


def apply_exit_evidence(
    position: PatternBreakoutPosition,
    evidence: Sequence[TechnicalExitEvidence],
) -> PatternBreakoutPosition:
    if position.state != PositionState.OPEN:
        return position
    actionable = [
        x for x in evidence
        if x.actionable and x.state not in {TechnicalExitState.HOLD, TechnicalExitState.NOT_EVALUABLE}
    ]
    if not actionable:
        return position

    earliest_date = min(x.evidence_date for x in actionable)
    same_day = [x for x in actionable if x.evidence_date == earliest_date]
    reasons = {x.state.value for x in same_day}
    if len(reasons) != 1:
        # Multiple independently actionable rules on the same evidence date are
        # deliberately fail-closed until explicit arbitration is source-locked.
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})

    x = same_day[0]
    if position.entry_date is None or x.evidence_date < position.entry_date:
        return PatternBreakoutPosition(
            **{**position.__dict__, "state": PositionState.NOT_EVALUABLE})
    return PatternBreakoutPosition(
        **{**position.__dict__,
           "state": PositionState.EXIT_PENDING,
           "exit_signal_date": x.evidence_date,
           "exit_reason": x.state.value})


def execute_pending_exit(
    position: PatternBreakoutPosition,
    *, next_session_date: Optional[date], next_open: Optional[float],
) -> PatternBreakoutPosition:
    if position.state != PositionState.EXIT_PENDING:
        return position
    if (
        position.exit_signal_date is None
        or next_session_date is None or next_session_date <= position.exit_signal_date
        or next_open is None or next_open <= 0
    ):
        return position
    return PatternBreakoutPosition(
        **{**position.__dict__,
           "state": PositionState.CLOSED,
           "exit_date": next_session_date,
           "exit_price": float(next_open)})
