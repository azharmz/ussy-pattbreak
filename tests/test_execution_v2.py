from datetime import date
import pytest
from pattern_breakout.entry_v2 import decide_event_t1_open
from pattern_breakout.execution_v2 import arbitrate_security_execution
from pattern_breakout.lifecycle_v2 import open_from_security_execution
def e(event,pivot,price=102):
 return decide_event_t1_open(event_id=event,security_id="XYZ",signal_date=date(2026,9,17),pivot_level=pivot,next_session_date=date(2026,9,18),next_open=price)
def test_multiple_pivots_collapse_to_one_execution_and_position():
 x=arbitrate_security_execution([e("a",100),e("b",101)])
 assert x.security_id=="XYZ" and x.fill_price==102
 assert x.supporting_event_ids==("a","b") and x.supporting_pivots==(100.0,101.0)
 p=open_from_security_execution(x);assert p.state=="OPEN";assert p.supporting_event_ids==("a","b")
def test_nonexecuted_event_does_not_create_execution():
 assert arbitrate_security_execution([e("a",110)]) is None
def test_duplicate_event_fails_closed():
 with pytest.raises(ValueError):arbitrate_security_execution([e("a",100),e("a",101)])
def test_conflicting_observed_fill_fails_closed():
 with pytest.raises(ValueError):arbitrate_security_execution([e("a",100,102),e("b",100,103)])
def test_position_identity_is_not_event_identity():
 x=arbitrate_security_execution([e("a",100),e("b",101)]);p=open_from_security_execution(x)
 assert p.position_id.startswith("position_") and p.position_id not in p.supporting_event_ids and p.execution_id!=p.position_id
