from datetime import date

from pattern_breakout.exit_v1 import (
    DailyTechnicalObservation, PositionTechnicalContext, TechnicalExitState,
    WeeklyTechnicalObservation, evaluate_daily_technical_exit,
    evaluate_weekly_10w_ma_exit,
)


ENTRY = date(2026, 9, 1)


def position():
    return PositionTechnicalContext(
        position_id="pos-1", security_id="XYZ", entry_date=ENTRY,
        purchase_price=102.0, proper_buy_point=100.0)


def test_defensive_loss_uses_actual_purchase_price():
    x = evaluate_daily_technical_exit(
        position=position(),
        observation=DailyTechnicalObservation(date(2026, 9, 8), close=93.84))
    assert x.state == TechnicalExitState.DEFENSIVE_LOSS
    assert x.actionable is True
    assert x.reference_level == 93.84


def test_normal_profit_zone_is_measured_from_proper_buy_point():
    x = evaluate_daily_technical_exit(
        position=position(),
        observation=DailyTechnicalObservation(date(2026, 9, 8), close=120.0))
    assert x.state == TechnicalExitState.NORMAL_PROFIT_ZONE
    assert x.actionable is True


def test_below_profit_zone_and_above_loss_is_hold():
    x = evaluate_daily_technical_exit(
        position=position(),
        observation=DailyTechnicalObservation(date(2026, 9, 8), close=110.0))
    assert x.state == TechnicalExitState.HOLD
    assert x.actionable is False


def test_weekly_10w_ma_violation_requires_above_normal_volume():
    base = dict(week_end_date=date(2026, 9, 11), close=95.0, ma_10w=96.0)
    hit = evaluate_weekly_10w_ma_exit(
        position=position(),
        observation=WeeklyTechnicalObservation(**base, volume=1_200_000, average_volume=1_000_000))
    miss = evaluate_weekly_10w_ma_exit(
        position=position(),
        observation=WeeklyTechnicalObservation(**base, volume=900_000, average_volume=1_000_000))
    assert hit.state == TechnicalExitState.TEN_WEEK_MA_VIOLATION
    assert hit.actionable is True
    assert miss.state == TechnicalExitState.HOLD


def test_incomplete_daily_or_weekly_period_fails_closed():
    d = evaluate_daily_technical_exit(
        position=position(),
        observation=DailyTechnicalObservation(date(2026, 9, 8), close=90.0, completed_bar=False))
    w = evaluate_weekly_10w_ma_exit(
        position=position(),
        observation=WeeklyTechnicalObservation(
            date(2026, 9, 11), close=90.0, ma_10w=96.0,
            volume=2_000_000, average_volume=1_000_000, completed_week=False))
    assert d.state == TechnicalExitState.NOT_EVALUABLE
    assert w.state == TechnicalExitState.NOT_EVALUABLE


def test_contract_contains_no_forbidden_or_deferred_exit_inputs():
    fields = set(PositionTechnicalContext.__dataclass_fields__)
    forbidden = {
        "max_hold", "atr", "r_target", "round_trip", "climax_top",
        "upper_channel_line", "deterioration_score",
    }
    assert fields.isdisjoint(forbidden)
