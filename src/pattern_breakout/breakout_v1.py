"""Pattern Breakout Core v1 breakout-confirmation contract.

Consumes a frozen O'Neil morphology assessment. This module does not detect or
tune patterns; it only converts an accepted frozen assessment plus completed
daily-bar breakout evidence into an independent technical candidate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

BREAKOUT_VERSION = "pattern-breakout-confirmation-v1"
MORPHOLOGY_SCHEMA = "oneil-pattern-output-v2"
MORPHOLOGY_ENGINE = "33-core-p8-frozen-v1"
TECHNICAL_CANDIDATE_STAGE = "TECHNICAL_BREAKOUT_CANDIDATE"
BREAKOUT_VOLUME_MIN_RATIO = 1.40
SUPPORTED_PATTERNS = frozenset({
    "CUP_WITH_HANDLE",
    "CUP_WITHOUT_HANDLE",
    "DOUBLE_BOTTOM",
    "FLAT_BASE",
})


class BreakoutState(str, Enum):
    TECHNICAL_BREAKOUT_CANDIDATE = TECHNICAL_CANDIDATE_STAGE
    PATTERN_NOT_ACCEPTED = "PATTERN_NOT_ACCEPTED"
    PIVOT_NOT_CROSSED = "PIVOT_NOT_CROSSED"
    VOLUME_NOT_CONFIRMED = "VOLUME_NOT_CONFIRMED"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class FrozenOneilAssessment:
    assessment_id: str
    security_id: str
    assessment_date: date
    pattern_type: str
    pattern_accepted: bool
    pivot_level: Optional[float]
    schema_version: str = MORPHOLOGY_SCHEMA
    engine_version: str = MORPHOLOGY_ENGINE
    ambiguous: bool = False
    rejected: bool = False


@dataclass(frozen=True)
class BreakoutObservation:
    bar_date: date
    prior_close: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    prior_50_volume_mean: Optional[float]
    completed_bar: bool = True


@dataclass(frozen=True)
class PatternBreakoutCandidate:
    candidate_id: str
    security_id: str
    signal_date: date
    pattern_type: str
    pivot_level: Optional[float]
    breakout_volume_ratio: Optional[float]
    pivot_crossed: bool
    breakout_state: BreakoutState
    candidate_stage: Optional[str]
    breakout_version: str = BREAKOUT_VERSION
    morphology_schema: str = MORPHOLOGY_SCHEMA
    morphology_engine: str = MORPHOLOGY_ENGINE


def _not_evaluable(a: FrozenOneilAssessment, o: BreakoutObservation) -> PatternBreakoutCandidate:
    return PatternBreakoutCandidate(
        candidate_id=a.assessment_id, security_id=a.security_id,
        signal_date=o.bar_date, pattern_type=a.pattern_type,
        pivot_level=a.pivot_level, breakout_volume_ratio=None,
        pivot_crossed=False, breakout_state=BreakoutState.NOT_EVALUABLE,
        candidate_stage=None,
    )


def decide_technical_breakout_candidate(
    *, assessment: FrozenOneilAssessment, observation: BreakoutObservation
) -> PatternBreakoutCandidate:
    """Evaluate only completed-bar breakout evidence, causally at bar T."""
    if (
        assessment.schema_version != MORPHOLOGY_SCHEMA
        or assessment.engine_version != MORPHOLOGY_ENGINE
        or observation.bar_date != assessment.assessment_date
        or not observation.completed_bar
    ):
        return _not_evaluable(assessment, observation)

    if (
        assessment.pattern_type not in SUPPORTED_PATTERNS
        or not assessment.pattern_accepted
        or assessment.ambiguous
        or assessment.rejected
    ):
        return PatternBreakoutCandidate(
            candidate_id=assessment.assessment_id, security_id=assessment.security_id,
            signal_date=observation.bar_date, pattern_type=assessment.pattern_type,
            pivot_level=assessment.pivot_level, breakout_volume_ratio=None,
            pivot_crossed=False, breakout_state=BreakoutState.PATTERN_NOT_ACCEPTED,
            candidate_stage=None,
        )

    pivot = assessment.pivot_level
    if (
        pivot is None or pivot <= 0
        or observation.prior_close is None or observation.prior_close <= 0
        or observation.close is None or observation.close <= 0
        or observation.volume is None or observation.volume < 0
        or observation.prior_50_volume_mean is None
        or observation.prior_50_volume_mean <= 0
    ):
        return _not_evaluable(assessment, observation)

    pivot_crossed = observation.prior_close <= pivot < observation.close
    ratio = observation.volume / observation.prior_50_volume_mean

    if not pivot_crossed:
        state = BreakoutState.PIVOT_NOT_CROSSED
        stage = None
    elif ratio < BREAKOUT_VOLUME_MIN_RATIO:
        state = BreakoutState.VOLUME_NOT_CONFIRMED
        stage = None
    else:
        state = BreakoutState.TECHNICAL_BREAKOUT_CANDIDATE
        stage = TECHNICAL_CANDIDATE_STAGE

    return PatternBreakoutCandidate(
        candidate_id=assessment.assessment_id, security_id=assessment.security_id,
        signal_date=observation.bar_date, pattern_type=assessment.pattern_type,
        pivot_level=float(pivot), breakout_volume_ratio=ratio,
        pivot_crossed=pivot_crossed, breakout_state=state,
        candidate_stage=stage,
    )
