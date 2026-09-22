"""Breakout v2 event-scoped T+1 execution contract."""
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional
BUY_ZONE_MAX_EXTENSION=0.05
VERSION="pattern-breakout-event-entry-v2"
class EventEntryState(str,Enum):
    NO_NEXT_SESSION_BAR="NO_NEXT_SESSION_BAR"
    EXECUTED_T1_OPEN="EXECUTED_T1_OPEN"
    MISSED_EXTENDED_AT_OPEN="MISSED_EXTENDED_AT_OPEN"
    BELOW_PIVOT_AT_OPEN="BELOW_PIVOT_AT_OPEN"
    NOT_EVALUABLE="NOT_EVALUABLE"
@dataclass(frozen=True)
class BreakoutEventEntry:
    event_id:str; security_id:str; signal_date:date; pivot_level:float
    next_session_date:Optional[date]; next_open:Optional[float]
    buy_zone_floor:float; buy_zone_ceiling:float; open_extension_pct:Optional[float]
    entry_state:EventEntryState; fill_date:Optional[date]; fill_price:Optional[float]
    fill_source:Optional[str]; entry_version:str=VERSION
def decide_event_t1_open(*,event_id,security_id,signal_date,pivot_level,next_session_date,next_open):
    if not event_id or pivot_level is None or float(pivot_level)<=0: raise ValueError("event_id and positive pivot required")
    p=float(pivot_level); ceiling=p*(1+BUY_ZONE_MAX_EXTENSION)
    common=dict(event_id=event_id,security_id=str(security_id),signal_date=signal_date,pivot_level=p,next_session_date=next_session_date,next_open=next_open,buy_zone_floor=p,buy_zone_ceiling=ceiling)
    if next_session_date is None or next_open is None:
        return BreakoutEventEntry(**common,open_extension_pct=None,entry_state=EventEntryState.NO_NEXT_SESSION_BAR,fill_date=None,fill_price=None,fill_source=None)
    if next_session_date<=signal_date: raise ValueError("next session must be after signal")
    o=float(next_open)
    if o<=0:return BreakoutEventEntry(**common,open_extension_pct=None,entry_state=EventEntryState.NOT_EVALUABLE,fill_date=None,fill_price=None,fill_source=None)
    ext=o/p-1
    if o<p: state=EventEntryState.BELOW_PIVOT_AT_OPEN
    elif o>ceiling: state=EventEntryState.MISSED_EXTENDED_AT_OPEN
    else: state=EventEntryState.EXECUTED_T1_OPEN
    fill=o if state==EventEntryState.EXECUTED_T1_OPEN else None
    return BreakoutEventEntry(**common,open_extension_pct=ext,entry_state=state,fill_date=next_session_date if fill is not None else None,fill_price=fill,fill_source="DAILY_OHLCV_OPEN" if fill is not None else None)
