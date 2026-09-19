from datetime import date

from pattern_breakout.breakout_v1 import (
    BreakoutObservation, BreakoutState, FrozenOneilAssessment,
    decide_technical_breakout_candidate,
)
from pattern_breakout.entry_v1 import EntryState, decide_pattern_breakout_t1_open


def test_confirmed_breakout_wires_directly_to_t1_entry_contract():
    signal_date = date(2026, 9, 18)
    candidate = decide_technical_breakout_candidate(
        assessment=FrozenOneilAssessment(
            assessment_id="pb-1", security_id="XYZ", assessment_date=signal_date,
            pattern_type="FLAT_BASE", pattern_accepted=True, pivot_level=100.0),
        observation=BreakoutObservation(
            bar_date=signal_date, prior_close=99.0, close=101.0,
            volume=1_500_000.0, prior_50_volume_mean=1_000_000.0),
    )
    assert candidate.breakout_state == BreakoutState.TECHNICAL_BREAKOUT_CANDIDATE

    entry = decide_pattern_breakout_t1_open(
        candidate_id=candidate.candidate_id,
        security_id=candidate.security_id,
        signal_date=candidate.signal_date,
        candidate_stage=candidate.candidate_stage,
        pivot_level=candidate.pivot_level,
        next_session_date=date(2026, 9, 21),
        next_open=102.0,
    )
    assert entry.entry_state == EntryState.EXECUTED_T1_OPEN
    assert entry.fill_price == 102.0
