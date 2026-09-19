from datetime import date

from pattern_breakout.entry_v1 import decide_pattern_breakout_t1_open, TECHNICAL_ELIGIBLE_STAGE
from pattern_breakout.exit_v1 import TechnicalExitEvidence, TechnicalExitState
from pattern_breakout.lifecycle_v1 import (
    PositionState, apply_exit_evidence, execute_pending_exit, open_from_entry,
)


def opened():
    e = decide_pattern_breakout_t1_open(
        candidate_id="pb-1", security_id="XYZ", signal_date=date(2026, 9, 17),
        candidate_stage=TECHNICAL_ELIGIBLE_STAGE, pivot_level=100.0,
        next_session_date=date(2026, 9, 18), next_open=102.0)
    return open_from_entry(e)


def evidence(day, state, actionable=True):
    return TechnicalExitEvidence(
        position_id="position:pb-1", security_id="XYZ", evidence_date=day,
        state=state, actionable=actionable, reference_level=100.0,
        observed_price=95.0, provenance="TEST")


def test_executed_entry_opens_position():
    p = opened()
    assert p.state == PositionState.OPEN
    assert p.entry_price == 102.0


def test_hold_evidence_keeps_position_open_without_time_exit():
    p = apply_exit_evidence(opened(), [
        evidence(date(2027, 9, 18), TechnicalExitState.HOLD, False)])
    assert p.state == PositionState.OPEN


def test_actionable_exit_is_pending_then_executes_next_open():
    p = apply_exit_evidence(opened(), [
        evidence(date(2026, 9, 21), TechnicalExitState.DEFENSIVE_LOSS)])
    assert p.state == PositionState.EXIT_PENDING
    assert p.exit_reason == TechnicalExitState.DEFENSIVE_LOSS.value
    closed = execute_pending_exit(
        p, next_session_date=date(2026, 9, 22), next_open=93.0)
    assert closed.state == PositionState.CLOSED
    assert closed.exit_date == date(2026, 9, 22)
    assert closed.exit_price == 93.0


def test_exit_cannot_fill_on_signal_day():
    p = apply_exit_evidence(opened(), [
        evidence(date(2026, 9, 21), TechnicalExitState.DEFENSIVE_LOSS)])
    same_day = execute_pending_exit(
        p, next_session_date=date(2026, 9, 21), next_open=93.0)
    assert same_day.state == PositionState.EXIT_PENDING


def test_earliest_actionable_evidence_wins():
    p = apply_exit_evidence(opened(), [
        evidence(date(2026, 9, 24), TechnicalExitState.NORMAL_PROFIT_ZONE),
        evidence(date(2026, 9, 21), TechnicalExitState.DEFENSIVE_LOSS),
    ])
    assert p.exit_signal_date == date(2026, 9, 21)
    assert p.exit_reason == TechnicalExitState.DEFENSIVE_LOSS.value


def test_same_day_conflicting_actions_fail_closed():
    p = apply_exit_evidence(opened(), [
        evidence(date(2026, 9, 21), TechnicalExitState.DEFENSIVE_LOSS),
        evidence(date(2026, 9, 21), TechnicalExitState.TEN_WEEK_MA_VIOLATION),
    ])
    assert p.state == PositionState.NOT_EVALUABLE


def test_lifecycle_has_no_max_hold():
    assert "max_hold" not in opened().__dataclass_fields__
