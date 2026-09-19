from datetime import date

from pattern_breakout.exit_arbitration_v1 import ArbitrationState, ExitArbitration
from pattern_breakout.exit_v1 import TechnicalExitEvidence, TechnicalExitState
from pattern_breakout.lifecycle_arbitration_v1 import apply_exit_arbitration
from pattern_breakout.lifecycle_v1 import PatternBreakoutPosition, PositionState, execute_pending_exit


def position():
    return PatternBreakoutPosition(
        position_id="p", candidate_id="c", security_id="XYZ",
        entry_date=date(2026, 9, 18), entry_price=102.0, pivot_level=100.0,
        state=PositionState.OPEN)


def evidence(state=TechnicalExitState.DEFENSIVE_LOSS):
    return TechnicalExitEvidence(
        "p", "XYZ", date(2026, 10, 1), state, True, 94.86, 94.0, "test")


def test_action_exit_schedules_next_open_not_same_bar():
    p = apply_exit_arbitration(
        position(), ExitArbitration(ArbitrationState.ACTION_EXIT, evidence(), "test"))
    assert p.state == PositionState.EXIT_PENDING
    same = execute_pending_exit(
        p, next_session_date=date(2026, 10, 1), next_open=93.5)
    assert same.state == PositionState.EXIT_PENDING
    nxt = execute_pending_exit(
        p, next_session_date=date(2026, 10, 2), next_open=93.5)
    assert nxt.state == PositionState.CLOSED
    assert nxt.exit_price == 93.5


def test_eight_week_profit_block_leaves_position_open():
    p = apply_exit_arbitration(
        position(), ExitArbitration(
            ArbitrationState.PROFIT_TAKING_BLOCKED_BY_EIGHT_WEEK_RULE,
            None, "test"))
    assert p.state == PositionState.OPEN


def test_hold_leaves_position_open_without_time_exit():
    p = apply_exit_arbitration(
        position(), ExitArbitration(ArbitrationState.HOLD, None, "test"))
    assert p.state == PositionState.OPEN


def test_not_evaluable_fails_position_closed_to_not_evaluable():
    p = apply_exit_arbitration(
        position(), ExitArbitration(ArbitrationState.NOT_EVALUABLE, None, "test"))
    assert p.state == PositionState.NOT_EVALUABLE


def test_selected_evidence_must_match_position_identity():
    bad = TechnicalExitEvidence(
        "other", "XYZ", date(2026, 10, 1),
        TechnicalExitState.DEFENSIVE_LOSS, True, 94.86, 94.0, "test")
    p = apply_exit_arbitration(
        position(), ExitArbitration(ArbitrationState.ACTION_EXIT, bad, "test"))
    assert p.state == PositionState.NOT_EVALUABLE
