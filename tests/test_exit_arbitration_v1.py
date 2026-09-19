from datetime import date
from pattern_breakout.eight_week_rule_v1 import EightWeekAssessment, EightWeekState
from pattern_breakout.exit_arbitration_v1 import ArbitrationState, arbitrate_exit
from pattern_breakout.exit_v1 import TechnicalExitEvidence, TechnicalExitState


def ev(state, actionable):
    return TechnicalExitEvidence(
        "p", "XYZ", date(2026, 10, 1), state, actionable,
        120.0, 121.0, "test")


def ew(state, week):
    return EightWeekAssessment(state, date(2026, 9, 25) if state != EightWeekState.NOT_QUALIFIED else None, 1, week, "test")


def test_active_eight_week_rule_blocks_profit_taking():
    x = arbitrate_exit([ev(TechnicalExitState.NORMAL_PROFIT_ZONE, False)],
                       ew(EightWeekState.QUALIFIED_HOLD, 4))
    assert x.state == ArbitrationState.PROFIT_TAKING_BLOCKED_BY_EIGHT_WEEK_RULE


def test_defensive_loss_is_not_blocked_by_eight_week_rule():
    x = arbitrate_exit([ev(TechnicalExitState.DEFENSIVE_LOSS, True)],
                       ew(EightWeekState.QUALIFIED_HOLD, 4))
    assert x.state == ArbitrationState.ACTION_EXIT
    assert x.selected.state == TechnicalExitState.DEFENSIVE_LOSS


def test_10w_sell_is_not_blocked_by_eight_week_rule():
    x = arbitrate_exit([ev(TechnicalExitState.TEN_WEEK_MA_VIOLATION, True)],
                       ew(EightWeekState.QUALIFIED_HOLD, 6))
    assert x.state == ArbitrationState.ACTION_EXIT


def test_profit_zone_waits_while_first_three_week_qualification_window_open():
    x = arbitrate_exit([ev(TechnicalExitState.NORMAL_PROFIT_ZONE, False)],
                       ew(EightWeekState.NOT_QUALIFIED, 2))
    assert x.state == ArbitrationState.HOLD


def test_profit_zone_actionable_after_week_three_if_never_qualified():
    x = arbitrate_exit([ev(TechnicalExitState.NORMAL_PROFIT_ZONE, False)],
                       ew(EightWeekState.NOT_QUALIFIED, 4))
    assert x.state == ArbitrationState.ACTION_EXIT


def test_profit_zone_actionable_after_qualified_minimum_hold_completed():
    x = arbitrate_exit([ev(TechnicalExitState.NORMAL_PROFIT_ZONE, False)],
                       ew(EightWeekState.HOLD_PERIOD_COMPLETE, 9))
    assert x.state == ArbitrationState.ACTION_EXIT


def test_simultaneous_independent_exit_reasons_fail_closed():
    x = arbitrate_exit([
        ev(TechnicalExitState.DEFENSIVE_LOSS, True),
        ev(TechnicalExitState.TEN_WEEK_MA_VIOLATION, True),
    ], ew(EightWeekState.QUALIFIED_HOLD, 4))
    assert x.state == ArbitrationState.NOT_EVALUABLE
