"""Source-locked arbitration between exit evidence and eight-week state.

The eight-week rule protects ordinary profit-taking only. It does not suppress
defensive-loss or independent technical sell evidence.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

from .eight_week_rule_v1 import EightWeekAssessment, EightWeekState
from .exit_v1 import TechnicalExitEvidence, TechnicalExitState

ARBITRATION_VERSION = "pattern-breakout-exit-arbitration-v1"


class ArbitrationState(str, Enum):
    HOLD = "HOLD"
    ACTION_EXIT = "ACTION_EXIT"
    PROFIT_TAKING_BLOCKED_BY_EIGHT_WEEK_RULE = "PROFIT_TAKING_BLOCKED_BY_EIGHT_WEEK_RULE"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class ExitArbitration:
    state: ArbitrationState
    selected: Optional[TechnicalExitEvidence]
    provenance: str
    version: str = ARBITRATION_VERSION


def arbitrate_exit(
    evidence: Iterable[TechnicalExitEvidence],
    eight_week: EightWeekAssessment,
) -> ExitArbitration:
    xs = list(evidence)
    if not xs or eight_week.state == EightWeekState.NOT_EVALUABLE:
        return ExitArbitration(
            ArbitrationState.NOT_EVALUABLE, None, "ENGINEERING_FAIL_CLOSED")

    # Independent risk/technical exits are never blocked by the profit exception.
    hard = [x for x in xs if x.actionable and x.state in {
        TechnicalExitState.DEFENSIVE_LOSS,
        TechnicalExitState.TEN_WEEK_MA_VIOLATION,
    }]
    if len(hard) > 1:
        # No arbitrary priority between simultaneous independent sell reasons.
        return ExitArbitration(
            ArbitrationState.NOT_EVALUABLE, None,
            "MULTIPLE_INDEPENDENT_ACTIONABLE_EXITS_REQUIRE_EXPLICIT_ARBITRATION")
    if hard:
        return ExitArbitration(
            ArbitrationState.ACTION_EXIT, hard[0],
            "INDEPENDENT_RISK_OR_TECHNICAL_SELL_EVIDENCE")

    profit = [x for x in xs if x.state == TechnicalExitState.NORMAL_PROFIT_ZONE]
    if profit:
        if eight_week.state == EightWeekState.QUALIFIED_HOLD:
            return ExitArbitration(
                ArbitrationState.PROFIT_TAKING_BLOCKED_BY_EIGHT_WEEK_RULE, None,
                "ORIGINAL_IBD_RAPID_WINNER_MINIMUM_HOLD_ACTIVE")
        # Profit evidence becomes actionable only once rapid-winner qualification
        # is impossible (after week 3 without qualification), or a qualified
        # position has completed the minimum eight-week hold.
        if (eight_week.state == EightWeekState.HOLD_PERIOD_COMPLETE
                or (eight_week.state == EightWeekState.NOT_QUALIFIED
                    and eight_week.current_week > 3)):
            chosen = profit[0]
            return ExitArbitration(
                ArbitrationState.ACTION_EXIT, chosen,
                "ORIGINAL_IBD_NORMAL_PROFIT_ZONE_ACTIONABLE_AFTER_EXCEPTION_RESOLUTION")
        return ExitArbitration(
            ArbitrationState.HOLD, None,
            "PROFIT_ZONE_EVIDENCE_PENDING_RAPID_WINNER_QUALIFICATION_WINDOW")

    return ExitArbitration(
        ArbitrationState.HOLD, None, "NO_ACTIONABLE_SOURCE_LOCKED_EXIT")
