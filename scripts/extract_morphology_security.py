"""Extract a small, lineage-preserving morphology audit slice for one security.

Diagnostic only: this does not alter candidate semantics or production checkpoints.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


KEEP = (
    "assessment_id",
    "security_id",
    "asof_date",
    "pattern",
    "normalized_status",
    "candidate_semantics",
    "base_id",
    "lineage_id",
    "structural_signature",
    "structural_start",
    "structural_end",
    "pivot_source_date",
    "pivot_level",
    "depth_pct",
    "faults",
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="upstream/raw-oneil-morphology.jsonl")
    ap.add_argument("--security-id", required=True)
    ap.add_argument("--output", default="audit/morphology-security.jsonl")
    args = ap.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with src.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if str(row.get("security_id")) != args.security_id:
                continue
            rows.append({key: row.get(key) for key in KEEP})

    rows.sort(key=lambda x: (
        str(x.get("pivot_level") or ""),
        str(x.get("pattern") or ""),
        str(x.get("structural_start") or ""),
        str(x.get("assessment_id") or ""),
    ))
    with dst.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    summary = {
        "security_id": args.security_id,
        "record_count": len(rows),
        "recognized_count": sum(r.get("normalized_status") == "RECOGNIZED" for r in rows),
        "output": str(dst),
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
