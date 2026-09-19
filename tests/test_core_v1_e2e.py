from datetime import date

from pattern_breakout.breakout_v1 import (
    BreakoutObservation, BreakoutState, FrozenOneilAssessment,
    decide_technical_breakout_candidate,
)
from pattern_breakout.entry_v1 import EntryState, decide_pattern_breakout_t1_open
from pattern_breakout.exit_v1 import (
    DailyTechnicalObservation, PositionTechnicalContext, TechnicalExitState,
    evaluate_daily_technical_exit,
)
from pattern_breakout.lifecycle_v1 import (
    PositionState, apply_exit_evidence, execute_pending_exit, open_from_entry,
)


def test_core_v1_full_causal_path_breakout_to_closed_position():
    signal = date(2026, 9, 17)

    candidate = decide_technical_breakout_candidate(
        assessment=FrozenOneilAssessment(
            assessment_id="oneil-XYZ-20260917", security_id="XYZ",
            assessment_date=signal, pattern_type="CUP_WITH_HANDLE",
            pattern_accepted=True, pivot_level=100.0),
        observation=BreakoutObservation(
            bar_date=signal, prior_close=99.0, close=101.0,
            volume=1_500_000.0, prior_50_volume_mean=1_000_000.0))
    assert candidate.breakout_state == BreakoutState.TECHNICAL_BREAKOUT_CANDIDATE

    entry = decide_pattern_breakout_t1_open(
        candidate_id=candidate.candidate_id, security_id=candidate.security_id,
        signal_date=candidate.signal_date, candidate_stage=candidate.candidate_stage,
        pivot_level=candidate.pivot_level, next_session_date=date(2026, 9, 18),
        next_open=102.0)
    assert entry.entry_state == EntryState.EXECUTED_T1_OPEN

    position = open_from_entry(entry)
    assert position.state == PositionState.OPEN

    exit_evidence = evaluate_daily_technical_exit(
        position=PositionTechnicalContext(
            position_id=position.position_id, security_id=position.security_id,
            entry_date=position.entry_date, purchase_price=position.entry_price,
            proper_buy_point=position.pivot_level),
        observation=DailyTechnicalObservation(
            observation_date=date(2026, 9, 21), close=93.0))
    assert exit_evidence.state == TechnicalExitState.DEFENSIVE_LOSS

    pending = apply_exit_evidence(position, [exit_evidence])
    assert pending.state == PositionState.EXIT_PENDING

    closed = execute_pending_exit(
        pending, next_session_date=date(2026, 9, 22), next_open=92.5)
    assert closed.state == PositionState.CLOSED
    assert closed.entry_date == date(2026, 9, 18)
    assert closed.entry_price == 102.0
    assert closed.exit_date == date(2026, 9, 22)
    assert closed.exit_price == 92.5


def test_valid_signal_missed_extended_never_opens_position():
    signal = date(2026, 9, 17)
    candidate = decide_technical_breakout_candidate(
        assessment=FrozenOneilAssessment(
            assessment_id="oneil-ABC-20260917", security_id="ABC",
            assessment_date=signal, pattern_type="FLAT_BASE",
            pattern_accepted=True, pivot_level=100.0),
        observation=BreakoutObservation(
            bar_date=signal, prior_close=99.0, close=101.0,
            volume=1_500_000.0, prior_50_volume_mean=1_000_000.0))
    entry = decide_pattern_breakout_t1_open(
        candidate_id=candidate.candidate_id, security_id=candidate.security_id,
        signal_date=candidate.signal_date, candidate_stage=candidate.candidate_stage,
        pivot_level=candidate.pivot_level, next_session_date=date(2026, 9, 18),
        next_open=106.0)
    assert entry.entry_state == EntryState.MISSED_EXTENDED_AT_OPEN
    assert open_from_entry(entry).state == PositionState.NOT_OPENED


def test_unconfirmed_breakout_cannot_become_executed_entry():
    signal = date(2026, 9, 17)
    candidate = decide_technical_breakout_candidate(
        assessment=FrozenOneilAssessment(
            assessment_id="oneil-LOWVOL", security_id="LOW",
            assessment_date=signal, pattern_type="DOUBLE_BOTTOM",
            pattern_accepted=True, pivot_level=100.0),
        observation=BreakoutObservation(
            bar_date=signal, prior_close=99.0, close=101.0,
            volume=1_200_000.0, prior_50_volume_mean=1_000_000.0))
    assert candidate.candidate_stage is None
    entry = decide_pattern_breakout_t1_open(
        candidate_id=candidate.candidate_id, security_id=candidate.security_id,
        signal_date=candidate.signal_date, candidate_stage=candidate.candidate_stage,
        pivot_level=candidate.pivot_level, next_session_date=date(2026, 9, 18),
        next_open=101.0)
    assert entry.entry_state == EntryState.NOT_TECHNICAL_CANDIDATE
