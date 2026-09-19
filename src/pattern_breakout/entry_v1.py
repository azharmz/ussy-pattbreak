"""Pattern Breakout Core v1 causal T+1-open execution contract.

Technical-only. No CAN SLIM eligibility or fundamental dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

ENTRY_VERSION = "pattern-breakout-entry-v1"
TECHNICAL_ELIGIBLE_STAGE = "TECHNICAL_BREAKOUT_CANDIDATE"
BUY_ZONE_MAX_EXTENSION = 0.05


class EntryState(str, Enum):
    NOT_TECHNICAL_CANDIDATE = "NOT_TECHNICAL_CANDIDATE"
    NO_NEXT_SESSION_BAR = "NO_NEXT_SESSION_BAR"
    EXECUTED_T1_OPEN = "EXECUTED_T1_OPEN"
    MISSED_EXTENDED_AT_OPEN = "MISSED_EXTENDED_AT_OPEN"
    BELOW_PIVOT_AT_OPEN = "BELOW_PIVOT_AT_OPEN"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class PatternBreakoutEntry:
    candidate_id: str
    security_id: str
    signal_date: date
    candidate_stage: str
    pivot_level: Optional[float]
    next_session_date: Optional[date]
    next_open: Optional[float]
    buy_zone_floor: Optional[float]
    buy_zone_ceiling: Optional[float]
    open_extension_pct: Optional[float]
    entry_state: EntryState
    fill_date: Optional[date]
    fill_price: Optional[float]
    fill_source: Optional[str]
    entry_version: str = ENTRY_VERSION


def decide_pattern_breakout_t1_open(*, candidate_id: str, security_id: str,
    signal_date: date, candidate_stage: str, pivot_level: Optional[float],
    next_session_date: Optional[date], next_open: Optional[float]) -> PatternBreakoutEntry:
    common = dict(candidate_id=candidate_id, security_id=security_id,
        signal_date=signal_date, candidate_stage=candidate_stage,
        pivot_level=pivot_level, next_session_date=next_session_date, next_open=next_open)

    if candidate_stage != TECHNICAL_ELIGIBLE_STAGE:
        return PatternBreakoutEntry(**common, buy_zone_floor=None, buy_zone_ceiling=None,
            open_extension_pct=None, entry_state=EntryState.NOT_TECHNICAL_CANDIDATE,
            fill_date=None, fill_price=None, fill_source=None)
    if pivot_level is None or pivot_level <= 0:
        return PatternBreakoutEntry(**common, buy_zone_floor=None, buy_zone_ceiling=None,
            open_extension_pct=None, entry_state=EntryState.NOT_EVALUABLE,
            fill_date=None, fill_price=None, fill_source=None)

    floor = float(pivot_level)
    ceiling = floor * (1.0 + BUY_ZONE_MAX_EXTENSION)
    if next_session_date is None or next_open is None:
        return PatternBreakoutEntry(**common, buy_zone_floor=floor, buy_zone_ceiling=ceiling,
            open_extension_pct=None, entry_state=EntryState.NO_NEXT_SESSION_BAR,
            fill_date=None, fill_price=None, fill_source=None)
    if next_session_date <= signal_date:
        raise ValueError("next_session_date must be strictly after signal_date")

    open_price = float(next_open)
    if open_price <= 0:
        return PatternBreakoutEntry(**common, buy_zone_floor=floor, buy_zone_ceiling=ceiling,
            open_extension_pct=None, entry_state=EntryState.NOT_EVALUABLE,
            fill_date=None, fill_price=None, fill_source=None)

    extension = open_price / floor - 1.0
    if open_price < floor:
        state, fill = EntryState.BELOW_PIVOT_AT_OPEN, None
    elif open_price > ceiling:
        state, fill = EntryState.MISSED_EXTENDED_AT_OPEN, None
    else:
        state, fill = EntryState.EXECUTED_T1_OPEN, open_price

    return PatternBreakoutEntry(**common, buy_zone_floor=floor, buy_zone_ceiling=ceiling,
        open_extension_pct=extension, entry_state=state,
        fill_date=next_session_date if fill is not None else None, fill_price=fill,
        fill_source="DAILY_OHLCV_OPEN" if fill is not None else None)


def validate_pattern_breakout_entry(x: PatternBreakoutEntry) -> list[str]:
    findings: list[str] = []
    if x.entry_state == EntryState.EXECUTED_T1_OPEN:
        if x.candidate_stage != TECHNICAL_ELIGIBLE_STAGE:
            findings.append("EXECUTED_WITHOUT_TECHNICAL_CANDIDATE")
        if x.fill_date is None or x.fill_date <= x.signal_date:
            findings.append("NON_CAUSAL_FILL_DATE")
        if x.fill_price != x.next_open:
            findings.append("FILL_NOT_OBSERVED_T1_OPEN")
        if x.fill_price is None or x.buy_zone_floor is None or x.buy_zone_ceiling is None or not (
            x.buy_zone_floor <= x.fill_price <= x.buy_zone_ceiling
        ):
            findings.append("FILL_OUTSIDE_BUY_ZONE")
    return findings
