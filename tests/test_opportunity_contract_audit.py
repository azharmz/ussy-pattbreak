import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_opportunity_contract.py"
SPEC = importlib.util.spec_from_file_location("audit_opportunity_contract", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
audit = MODULE.audit


def row(a, base, lineage, security="1", pattern="FLAT_BASE", pivot=100, close=95):
    return {
        "assessment_id": a, "base_id": base, "lineage_id": lineage,
        "security_id": security, "pattern_type": pattern,
        "morphology_status": "RECOGNIZED", "pivot_level": pivot,
        "as_of_date": "2026-09-21", "as_of_close": close,
    }


def test_audit_preserves_identity_layers_without_inventing_opportunities():
    result = audit([
        row("a1", "b1", "l1"), row("a2", "b1", "l1"),
        row("a3", "b2", "l1", pivot=110, close=112),
    ])
    assert result["cardinality"] == {
        "assessment_rows": 3,
        "below_pivot_assessments": 2,
        "base_ids": 2,
        "setup_keys": 2,
        "lineage_ids": 1,
        "security_pattern_pivot_groups": 2,
        "event_shaped_groups_not_events": 2,
        "securities": 1,
    }
    assert result["identity_checks"]["base_ids_spanning_security_or_pivot"] == 0
    assert result["identity_checks"]["lineage_ids_spanning_security_or_pivot"] == 1
    assert result["decision"]["canonical_opportunity_supported"] is False
    assert result["decision"]["d1_current_opportunities_rows"] == 0


def test_audit_fails_closed_on_duplicate_assessment():
    with pytest.raises(ValueError, match="duplicate assessment_id"):
        audit([row("a1", "b1", "l1"), row("a1", "b2", "l2")])


def test_audit_fails_closed_when_setup_identity_is_missing():
    broken = row("a1", "b1", "l1")
    broken["base_id"] = None
    with pytest.raises(ValueError, match="missing base_id"):
        audit([broken])
