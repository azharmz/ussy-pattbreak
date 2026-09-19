from datetime import date

from pattern_breakout.breakout_v1 import (
    BREAKOUT_VOLUME_MIN_RATIO, BreakoutObservation, BreakoutState,
    FrozenOneilAssessment, TECHNICAL_CANDIDATE_STAGE,
    decide_technical_breakout_candidate,
)


D = date(2026, 9, 18)


def assessment(**overrides):
    x = dict(
        assessment_id="oneil-XYZ-20260918", security_id="XYZ",
        assessment_date=D, pattern_type="CUP_WITH_HANDLE",
        pattern_accepted=True, pivot_level=100.0,
    )
    x.update(overrides)
    return FrozenOneilAssessment(**x)


def observation(**overrides):
    x = dict(
        bar_date=D, prior_close=99.0, close=101.0,
        volume=1_400_000.0, prior_50_volume_mean=1_000_000.0,
        completed_bar=True,
    )
    x.update(overrides)
    return BreakoutObservation(**x)


def test_proper_pattern_crossed_pivot_and_volume_creates_candidate():
    x = decide_technical_breakout_candidate(
        assessment=assessment(), observation=observation())
    assert x.breakout_state == BreakoutState.TECHNICAL_BREAKOUT_CANDIDATE
    assert x.candidate_stage == TECHNICAL_CANDIDATE_STAGE
    assert x.pivot_crossed is True
    assert x.breakout_volume_ratio == BREAKOUT_VOLUME_MIN_RATIO


def test_pivot_not_crossed_is_not_candidate():
    x = decide_technical_breakout_candidate(
        assessment=assessment(), observation=observation(close=100.0))
    assert x.breakout_state == BreakoutState.PIVOT_NOT_CROSSED
    assert x.candidate_stage is None


def test_volume_below_140_percent_is_not_confirmed():
    x = decide_technical_breakout_candidate(
        assessment=assessment(), observation=observation(volume=1_399_999.0))
    assert x.breakout_state == BreakoutState.VOLUME_NOT_CONFIRMED
    assert x.candidate_stage is None


def test_ambiguous_or_rejected_pattern_is_not_candidate():
    for a in (assessment(ambiguous=True), assessment(rejected=True)):
        x = decide_technical_breakout_candidate(assessment=a, observation=observation())
        assert x.breakout_state == BreakoutState.PATTERN_NOT_ACCEPTED
        assert x.candidate_stage is None


def test_no_fundamental_or_canslim_inputs_exist():
    fields = set(FrozenOneilAssessment.__dataclass_fields__)
    assert "C_state" not in fields
    assert "A_state" not in fields
    assert "fundamental_state" not in fields
    assert "CANSLIM_ELIGIBLE" not in fields


def test_incomplete_bar_fails_closed():
    x = decide_technical_breakout_candidate(
        assessment=assessment(), observation=observation(completed_bar=False))
    assert x.breakout_state == BreakoutState.NOT_EVALUABLE
    assert x.candidate_stage is None


def test_wrong_frozen_engine_or_schema_fails_closed():
    for a in (
        assessment(schema_version="other-schema"),
        assessment(engine_version="other-engine"),
    ):
        x = decide_technical_breakout_candidate(assessment=a, observation=observation())
        assert x.breakout_state == BreakoutState.NOT_EVALUABLE


def test_assessment_and_observation_dates_must_match():
    x = decide_technical_breakout_candidate(
        assessment=assessment(),
        observation=observation(bar_date=date(2026, 9, 19)),
    )
    assert x.breakout_state == BreakoutState.NOT_EVALUABLE
