from datetime import date

import pytest

from pattern_breakout.extension_evidence_v1 import (
    CoreOpportunityIdentity,
    EvidenceState,
    ExtensionType,
    attach_extension_evidence,
)


def opportunity():
    return CoreOpportunityIdentity(
        security_id="NVDA",
        assessment_id="assessment-2026-09-18",
        base_id="base-1",
        lineage_id="lineage-1",
        as_of_date=date(2026, 9, 18),
        pattern_type="CUP_WITH_HANDLE",
        pivot_level=190.0,
    )


def test_extension_attaches_to_structural_observation_without_core_state():
    e = attach_extension_evidence(
        opportunity=opportunity(),
        extension_type=ExtensionType.MINERVINI_VCP_V1,
        extension_version="minervini-vcp-evidence-v1",
        evidence_state=EvidenceState.CONFIRMED,
        payload={"contraction_count": 3},
        source_hash="sha256:" + "a" * 64,
        methodology_lock="minervini-vcp-source-lock-v1",
    )
    assert e.opportunity.base_id == "base-1"
    assert e.opportunity.lineage_id == "lineage-1"
    assert e.evidence_state is EvidenceState.CONFIRMED
    assert not hasattr(e, "candidate_stage")
    assert not hasattr(e, "breakout_state")


def test_not_available_is_distinct_from_negative_evidence():
    e = attach_extension_evidence(
        opportunity=opportunity(),
        extension_type=ExtensionType.WEINSTEIN_V1,
        extension_version="weinstein-evidence-v1",
        evidence_state=EvidenceState.NOT_AVAILABLE,
        payload={},
        source_hash="sha256:" + "b" * 64,
        methodology_lock="weinstein-source-lock-v1",
    )
    assert e.evidence_state is EvidenceState.NOT_AVAILABLE
    assert e.evidence_state is not EvidenceState.NOT_CONFIRMED


def test_invalid_lineage_fails_closed():
    o = opportunity()
    bad = CoreOpportunityIdentity(
        security_id=o.security_id,
        assessment_id=o.assessment_id,
        base_id="",
        lineage_id=o.lineage_id,
        as_of_date=o.as_of_date,
        pattern_type=o.pattern_type,
        pivot_level=o.pivot_level,
    )
    with pytest.raises(ValueError):
        attach_extension_evidence(
            opportunity=bad,
            extension_type=ExtensionType.WEINSTEIN_V1,
            extension_version="weinstein-evidence-v1",
            evidence_state=EvidenceState.NOT_EVALUABLE,
            payload={},
            source_hash="sha256:" + "c" * 64,
            methodology_lock="weinstein-source-lock-v1",
        )
