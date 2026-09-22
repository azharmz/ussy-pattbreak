"""Security-level arbitration for executed v2 breakout events."""
from dataclasses import dataclass
from datetime import date
import hashlib,json
from typing import Sequence
from .entry_v2 import BreakoutEventEntry,EventEntryState
VERSION="pattern-breakout-security-execution-v2"
@dataclass(frozen=True)
class SecurityExecution:
 execution_id:str;security_id:str;signal_date:date;fill_date:date;fill_price:float
 supporting_event_ids:tuple[str,...];supporting_pivots:tuple[float,...]
 execution_version:str=VERSION
def _id(sid,day,price):
 raw=json.dumps([str(sid),day.isoformat(),format(float(price),".12g"),VERSION],separators=(",",":"))
 return "execution_"+hashlib.sha256(raw.encode()).hexdigest()[:32]
def arbitrate_security_execution(entries:Sequence[BreakoutEventEntry])->SecurityExecution|None:
 xs=[x for x in entries if x.entry_state==EventEntryState.EXECUTED_T1_OPEN]
 if not xs:return None
 sids={x.security_id for x in xs};signals={x.signal_date for x in xs};dates={x.fill_date for x in xs};prices={x.fill_price for x in xs}
 if len(sids)!=1 or len(signals)!=1:raise ValueError("arbitration group must be one security and signal date")
 if None in dates or None in prices or len(dates)!=1 or len(prices)!=1:raise ValueError("executed events disagree on observed fill")
 ids=[x.event_id for x in xs]
 if len(ids)!=len(set(ids)):raise ValueError("duplicate event_id in execution arbitration")
 sid=next(iter(sids));day=next(iter(dates));price=float(next(iter(prices)))
 return SecurityExecution(execution_id=_id(sid,day,price),security_id=sid,signal_date=next(iter(signals)),fill_date=day,fill_price=price,supporting_event_ids=tuple(sorted(ids)),supporting_pivots=tuple(sorted({float(x.pivot_level) for x in xs})))
