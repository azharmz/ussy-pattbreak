"""Economic position identity opened from one arbitrated v2 security execution."""
from dataclasses import dataclass
from datetime import date
import hashlib,json
from .execution_v2 import SecurityExecution
VERSION="pattern-breakout-position-v2"
@dataclass(frozen=True)
class PatternBreakoutPositionV2:
 position_id:str;execution_id:str;security_id:str;entry_date:date;entry_price:float
 supporting_event_ids:tuple[str,...];supporting_pivots:tuple[float,...]
 state:str="OPEN";lifecycle_version:str=VERSION
def open_from_security_execution(x:SecurityExecution)->PatternBreakoutPositionV2:
 raw=json.dumps([x.security_id,x.fill_date.isoformat(),format(x.fill_price,".12g"),VERSION],separators=(",",":"))
 pid="position_"+hashlib.sha256(raw.encode()).hexdigest()[:32]
 return PatternBreakoutPositionV2(position_id=pid,execution_id=x.execution_id,security_id=x.security_id,entry_date=x.fill_date,entry_price=x.fill_price,supporting_event_ids=x.supporting_event_ids,supporting_pivots=x.supporting_pivots)
