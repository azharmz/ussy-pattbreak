"""Causal state for the original IBD eight-week hold exception.

This is not a generic max-hold. It only qualifies a rapid winner when price
reaches >20% above the proper buy point within the first three breakout weeks.
The breakout week is week 1.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Optional


EIGHT_WEEK_RULE_VERSION = "ibd-eight-week-rule-v1"
RAPID_WINNER_GAIN = 0.20
QUALIFICATION_WEEKS = 3
HOLD_THROUGH_WEEK = 8


class EightWeekState(str, Enum):
    NOT_QUALIFIED = "NOT_QUALIFIED"
    QUALIFIED_HOLD = "QUALIFIED_HOLD"
    HOLD_PERIOD_COMPLETE = "HOLD_PERIOD_COMPLETE"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class EightWeekRuleContext:
    breakout_date: date
    proper_buy_point: float
    first_rapid_winner_date: Optional[date] = None


@dataclass(frozen=True)
class EightWeekAssessment:
    state: EightWeekState
    first_rapid_winner_date: Optional[date]
    breakout_week: int
    current_week: int
    provenance: str
    version: str = EIGHT_WEEK_RULE_VERSION


def _week_number(breakout_date: date, observation_date: date) -> int:
    # IBD week count is calendar/trading-week based with breakout week = week 1.
    # Monday anchors make the count stable across daily observations.
    b0 = breakout_date - timedelta(days=breakout_date.weekday())
    o0 = observation_date - timedelta(days=observation_date.weekday())
    return ((o0 - b0).days // 7) + 1


def assess_eight_week_rule(
    *,
    context: EightWeekRuleContext,
    observation_date: date,
    high: Optional[float],
    completed_bar: bool = True,
) -> EightWeekAssessment:
    if (not completed_bar or context.proper_buy_point <= 0
            or observation_date < context.breakout_date
            or high is None or high <= 0):
        return EightWeekAssessment(
            EightWeekState.NOT_EVALUABLE, context.first_rapid_winner_date,
            1, 0, "ENGINEERING_FAIL_CLOSED")

    week = _week_number(context.breakout_date, observation_date)
    first = context.first_rapid_winner_date
    threshold = context.proper_buy_point * (1.0 + RAPID_WINNER_GAIN)

    if first is None and week <= QUALIFICATION_WEEKS and high > threshold:
        first = observation_date

    if first is None:
        return EightWeekAssessment(
            EightWeekState.NOT_QUALIFIED, None, 1, week,
            "ORIGINAL_IBD_RAPID_WINNER_NOT_YET_QUALIFIED")

    if week <= HOLD_THROUGH_WEEK:
        return EightWeekAssessment(
            EightWeekState.QUALIFIED_HOLD, first, 1, week,
            "ORIGINAL_IBD_GAIN_OVER_20_WITHIN_THREE_WEEKS__HOLD_AT_LEAST_EIGHT_WEEKS")

    return EightWeekAssessment(
        EightWeekState.HOLD_PERIOD_COMPLETE, first, 1, week,
        "ORIGINAL_IBD_EIGHT_WEEK_MINIMUM_HOLD_COMPLETED")


def advance_context(
    context: EightWeekRuleContext, assessment: EightWeekAssessment
) -> EightWeekRuleContext:
    """Persist only causal qualification state for the next completed bar."""
    if assessment.state == EightWeekState.NOT_EVALUABLE:
        return context
    return EightWeekRuleContext(
        breakout_date=context.breakout_date,
        proper_buy_point=context.proper_buy_point,
        first_rapid_winner_date=assessment.first_rapid_winner_date,
    )
