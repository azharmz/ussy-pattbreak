"""Pattern Breakout Core v1 source-locked technical exit evidence.

No max-hold, fixed-R target, ATR exit, round-trip automation, climax-top
automation, or composite deterioration score is implemented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

EXIT_VERSION = "pattern-breakout-technical-exit-v1"
DEFENSIVE_LOSS_PCT = 0.08
NORMAL_PROFIT_ZONE_LOW = 0.20
NORMAL_PROFIT_ZONE_HIGH = 0.25


class TechnicalExitState(str, Enum):
    HOLD = "HOLD"
    DEFENSIVE_LOSS = "DEFENSIVE_LOSS"
    NORMAL_PROFIT_ZONE = "NORMAL_PROFIT_ZONE"
    TEN_WEEK_MA_VIOLATION = "TEN_WEEK_MA_VIOLATION"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class PositionTechnicalContext:
    position_id: str
    security_id: str
    entry_date: date
    purchase_price: float
    proper_buy_point: float


@dataclass(frozen=True)
class DailyTechnicalObservation:
    observation_date: date
    close: Optional[float]
    completed_bar: bool = True


@dataclass(frozen=True)
class WeeklyTechnicalObservation:
    week_end_date: date
    close: Optional[float]
    ma_10w: Optional[float]
    volume: Optional[float]
    average_volume: Optional[float]
    completed_week: bool = True


@dataclass(frozen=True)
class TechnicalExitEvidence:
    position_id: str
    security_id: str
    evidence_date: date
    state: TechnicalExitState
    actionable: bool
    reference_level: Optional[float]
    observed_price: Optional[float]
    provenance: str
    exit_version: str = EXIT_VERSION


def evaluate_daily_technical_exit(
    *, position: PositionTechnicalContext, observation: DailyTechnicalObservation
) -> TechnicalExitEvidence:
    """Evaluate source-locked daily evidence on a completed bar."""
    if (
        not observation.completed_bar
        or observation.observation_date < position.entry_date
        or position.purchase_price <= 0
        or position.proper_buy_point <= 0
        or observation.close is None
        or observation.close <= 0
    ):
        return TechnicalExitEvidence(
            position.position_id, position.security_id, observation.observation_date,
            TechnicalExitState.NOT_EVALUABLE, False, None, observation.close,
            "ENGINEERING_FAIL_CLOSED",
        )

    defensive_level = position.purchase_price * (1.0 - DEFENSIVE_LOSS_PCT)
    profit_floor = position.proper_buy_point * (1.0 + NORMAL_PROFIT_ZONE_LOW)
    profit_ceiling = position.proper_buy_point * (1.0 + NORMAL_PROFIT_ZONE_HIGH)

    if observation.close <= defensive_level:
        return TechnicalExitEvidence(
            position.position_id, position.security_id, observation.observation_date,
            TechnicalExitState.DEFENSIVE_LOSS, True, defensive_level, observation.close,
            "ORIGINAL_DEFENSIVE_LOSS_7_8_PERCENT__OPERATIONALIZED_AT_8_PERCENT",
        )

    if observation.close >= profit_floor:
        return TechnicalExitEvidence(
            position.position_id, position.security_id, observation.observation_date,
            TechnicalExitState.NORMAL_PROFIT_ZONE, True, profit_ceiling, observation.close,
            "ORIGINAL_NORMAL_PROFIT_ZONE_20_25_PERCENT",
        )

    return TechnicalExitEvidence(
        position.position_id, position.security_id, observation.observation_date,
        TechnicalExitState.HOLD, False, None, observation.close,
        "SOURCE_LOCKED_NO_ACTIONABLE_DAILY_EXIT",
    )


def evaluate_weekly_10w_ma_exit(
    *, position: PositionTechnicalContext, observation: WeeklyTechnicalObservation
) -> TechnicalExitEvidence:
    """Evaluate the frozen weekly 10-week-MA / above-normal-volume evidence."""
    if (
        not observation.completed_week
        or observation.week_end_date < position.entry_date
        or observation.close is None or observation.close <= 0
        or observation.ma_10w is None or observation.ma_10w <= 0
        or observation.volume is None or observation.volume < 0
        or observation.average_volume is None or observation.average_volume <= 0
    ):
        return TechnicalExitEvidence(
            position.position_id, position.security_id, observation.week_end_date,
            TechnicalExitState.NOT_EVALUABLE, False, None, observation.close,
            "ENGINEERING_FAIL_CLOSED",
        )

    if observation.close < observation.ma_10w and observation.volume > observation.average_volume:
        return TechnicalExitEvidence(
            position.position_id, position.security_id, observation.week_end_date,
            TechnicalExitState.TEN_WEEK_MA_VIOLATION, True, observation.ma_10w,
            observation.close, "ORIGINAL_WEEKLY_10W_MA_VIOLATION_ABOVE_NORMAL_VOLUME",
        )

    return TechnicalExitEvidence(
        position.position_id, position.security_id, observation.week_end_date,
        TechnicalExitState.HOLD, False, observation.ma_10w, observation.close,
        "SOURCE_LOCKED_NO_ACTIONABLE_WEEKLY_EXIT",
    )
