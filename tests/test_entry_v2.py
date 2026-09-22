from datetime import date
from pattern_breakout.entry_v2 import decide_event_t1_open,EventEntryState
def d(o):
 return decide_event_t1_open(event_id="event_x",security_id="S",signal_date=date(2026,9,17),pivot_level=100,next_session_date=date(2026,9,18),next_open=o)
def test_v2_event_entry_boundaries():
 assert d(99).entry_state==EventEntryState.BELOW_PIVOT_AT_OPEN
 assert d(100).entry_state==EventEntryState.EXECUTED_T1_OPEN
 assert d(105).entry_state==EventEntryState.EXECUTED_T1_OPEN
 assert d(105.01).entry_state==EventEntryState.MISSED_EXTENDED_AT_OPEN
def test_v2_identity_is_event_not_candidate():
 x=d(102);assert x.event_id=="event_x";assert not hasattr(x,"candidate_id");assert x.fill_price==102
