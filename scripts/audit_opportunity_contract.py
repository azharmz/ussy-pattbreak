"""Audit morphology serving cardinality without defining Opportunity eligibility.

This tool is read-only.  It deliberately calls pre-breakout rows ``assessments``
and structure groups ``setups``; neither is promoted to an Opportunity.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _key(row: dict, *names: str) -> tuple:
    return tuple(row.get(name) for name in names)


def audit(rows: list[dict]) -> dict:
    required = (
        "assessment_id", "base_id", "lineage_id", "security_id",
        "pattern_type", "pivot_level", "as_of_date", "as_of_close",
    )
    seen: set[str] = set()
    bases: dict[str, list[dict]] = defaultdict(list)
    lineages: dict[str, list[dict]] = defaultdict(list)
    below_pivot = 0
    logical_bytes = 0

    for row in rows:
        missing = [name for name in required if row.get(name) in (None, "")]
        if missing:
            raise ValueError(f"assessment missing {','.join(missing)}")
        assessment_id = str(row["assessment_id"])
        if assessment_id in seen:
            raise ValueError(f"duplicate assessment_id: {assessment_id}")
        seen.add(assessment_id)
        if row.get("morphology_status") != "RECOGNIZED":
            raise ValueError(f"non-RECOGNIZED assessment: {assessment_id}")
        if float(row["pivot_level"]) <= 0:
            raise ValueError(f"non-positive pivot: {assessment_id}")
        bases[str(row["base_id"])].append(row)
        lineages[str(row["lineage_id"])].append(row)
        below_pivot += float(row["as_of_close"]) < float(row["pivot_level"])
        logical_bytes += len(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()) + 1

    def variants(groups: dict[str, list[dict]], fields: tuple[str, ...]) -> int:
        return sum(len({_key(row, *fields) for row in group}) > 1 for group in groups.values())

    setup_keys = {
        _key(row, "security_id", "pattern_type", "pivot_level", "base_id")
        for row in rows
    }
    event_keys = {
        _key(row, "security_id", "as_of_date", "pivot_level") for row in rows
    }
    average = logical_bytes / len(rows) if rows else 0
    return {
        "semantics": {
            "assessment": "evidence",
            "base": "setup_lifecycle",
            "lineage": "ancestry_not_consumption_key",
            "event": "security_signal_date_exact_pivot",
        },
        "cardinality": {
            "assessment_rows": len(rows),
            "below_pivot_assessments": below_pivot,
            "base_ids": len(bases),
            "setup_keys": len(setup_keys),
            "lineage_ids": len(lineages),
            "security_pattern_pivot_groups": len({
                _key(row, "security_id", "pattern_type", "pivot_level") for row in rows
            }),
            "event_shaped_groups_not_events": len(event_keys),
            "securities": len({str(row["security_id"]) for row in rows}),
        },
        "identity_checks": {
            "base_ids_spanning_security_or_pivot": variants(
                bases, ("security_id", "pivot_level")
            ),
            "base_ids_spanning_patterns": variants(bases, ("pattern_type",)),
            "lineage_ids_spanning_security_or_pivot": variants(
                lineages, ("security_id", "pivot_level")
            ),
        },
        "impact": {
            "source_logical_bytes": logical_bytes,
            "average_source_row_bytes": round(average, 2),
            "d1_full_assessment_rows": len(rows),
            "d1_base_projection_rows": len(bases),
            "full_refresh_write_amplification_vs_base": (
                round(len(rows) / len(bases), 3) if bases else None
            ),
            "note": "D1 storage bytes are engine-dependent; row counts and logical payload bytes are the safe planning bounds.",
        },
        "decision": {
            "canonical_opportunity_supported": False,
            "reason": "No frozen Opportunity eligibility contract exists; below-pivot is a fact, not an actionable threshold.",
            "d1_current_opportunities_rows": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--expected-as-of")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.snapshot.read_text().splitlines() if line]
    if args.expected_as_of:
        dates = {row.get("as_of_date") for row in rows}
        if dates != {args.expected_as_of}:
            raise ValueError(f"snapshot as_of mismatch: {sorted(dates)}")
    result = audit(rows)
    body = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body)
    print(body, end="")


if __name__ == "__main__":
    main()
