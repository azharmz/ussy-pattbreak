from datetime import date
from pattern_breakout.eight_week_rule_v1 import (
    EightWeekRuleContext, EightWeekState, advance_context,
    assess_eight_week_rule,
)


def ctx():
    return EightWeekRuleContext(
        breakout_date=date(2026, 9, 17), proper_buy_point=100.0)


def test_more_than_20_percent_within_first_three_breakout_weeks_qualifies():
    a = assess_eight_week_rule(
        context=ctx(), observation_date=date(2026, 9, 25), high=120.01)
    assert a.state == EightWeekState.QUALIFIED_HOLD
    assert a.current_week == 2
    assert a.first_rapid_winner_date == date(2026, 9, 25)


def test_exactly_20_percent_does_not_satisfy_more_than_20_wording():
    a = assess_eight_week_rule(
        context=ctx(), observation_date=date(2026, 9, 25), high=120.0)
    assert a.state == EightWeekState.NOT_QUALIFIED


def test_first_reach_after_week_three_does_not_qualify():
    a = assess_eight_week_rule(
        context=ctx(), observation_date=date(2026, 10, 12), high=130.0)
    assert a.current_week == 5
    assert a.state == EightWeekState.NOT_QUALIFIED


def test_qualification_persists_even_if_price_later_falls_below_threshold():
    first = assess_eight_week_rule(
        context=ctx(), observation_date=date(2026, 9, 25), high=121.0)
    saved = advance_context(ctx(), first)
    later = assess_eight_week_rule(
        context=saved, observation_date=date(2026, 10, 9), high=110.0)
    assert later.state == EightWeekState.QUALIFIED_HOLD
    assert later.first_rapid_winner_date == date(2026, 9, 25)


def test_breakout_week_is_week_one_and_hold_completes_after_week_eight():
    first = assess_eight_week_rule(
        context=ctx(), observation_date=date(2026, 9, 18), high=121.0)
    saved = advance_context(ctx(), first)
    w8 = assess_eight_week_rule(
        context=saved, observation_date=date(2026, 11, 6), high=125.0)
    w9 = assess_eight_week_rule(
        context=saved, observation_date=date(2026, 11, 9), high=125.0)
    assert w8.current_week == 8 and w8.state == EightWeekState.QUALIFIED_HOLD
    assert w9.current_week == 9 and w9.state == EightWeekState.HOLD_PERIOD_COMPLETE


def test_no_generic_elapsed_time_qualification():
    a = assess_eight_week_rule(
        context=ctx(), observation_date=date(2027, 1, 8), high=119.0)
    assert a.state == EightWeekState.NOT_QUALIFIED


def test_incomplete_bar_fails_closed():
    a = assess_eight_week_rule(
        context=ctx(), observation_date=date(2026, 9, 18),
        high=130.0, completed_bar=False)
    assert a.state == EightWeekState.NOT_EVALUABLE
