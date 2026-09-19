"""Adapter from verified ussy-data READY v2 bytes to frozen O'Neil morphology.

The morphology package is intentionally imported from an externally pinned
checkout; this repository does not copy or modify detector code.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
import hashlib
import io
import json
from typing import Any

import pandas as pd

from .pipeline_v1 import CheckpointLineage, CheckpointStage

FROZEN_ONEIL_SHA = "c433cc1e35a5aa32a46f732cd8c5545935e36e40"
ONEIL_OUTPUT_SCHEMA = "oneil-pattern-output-v2"
ONEIL_ENGINE_VERSION = "33-core-p8-frozen-v1"
MORPHOLOGY_ADAPTER_VERSION = "pattern-breakout-frozen-morphology-adapter-v1"
REQUIRED_COLUMNS = (
    "date", "security_id", "ticker", "open", "high", "low",
    "close", "adj_close", "volume",
)


def ready_v2_frame(parquet_body: bytes, frozen_ready: dict[str, Any]) -> pd.DataFrame:
    """Materialize only the exact Parquet already proven by FROZEN_READY."""
    source_hash = frozen_ready.get("source_hash", "")
    if hashlib.sha256(parquet_body).hexdigest() != source_hash:
        raise ValueError("Parquet bytes do not match FROZEN_READY source_hash")
    if frozen_ready.get("stage") != CheckpointStage.FROZEN_READY.value:
        raise ValueError("expected FROZEN_READY checkpoint")
    if frozen_ready.get("schema_version") != "ussy-data-ready-v2":
        raise ValueError("unsupported READY schema")

    frame = pd.read_parquet(io.BytesIO(parquet_body))
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"READY dataset missing required columns: {sorted(missing)}")
    frame = frame.loc[:, REQUIRED_COLUMNS].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.tz_localize(None).dt.normalize()
    if frame.duplicated(["security_id", "date"]).any():
        raise ValueError("duplicate security/date rows")
    return frame.sort_values(["security_id", "date"]).reset_index(drop=True)


def run_frozen_morphology(
    *,
    parquet_body: bytes,
    frozen_ready: dict[str, Any],
    producer_commit: str,
    producer_run: str,
) -> tuple[dict[str, Any], str]:
    """Run frozen v2 engine against a verified READY v2 object and checkpoint JSONL."""
    # Import is delayed so ordinary unit tests do not require the external repo.
    from oneil_patterns.data.r2_ready import ReadyDataset
    from oneil_patterns.production.engine import analyze_security
    from oneil_patterns.production.runner import run_ready_dataset

    frame = ready_v2_frame(parquet_body, frozen_ready)
    asof = date.fromisoformat(frozen_ready["ready"]["as_of_date"])
    frame = frame.loc[frame["date"].dt.date <= asof].copy()
    dataset = ReadyDataset(frame=frame, manifest={
        "schema_version": 2,
        "parquet_key": frozen_ready["ready"]["parquet_key"],
        "sha256": frozen_ready["source_hash"],
        "security_ids": sorted(frame["security_id"].astype(str).unique().tolist()),
        "rows": len(frame),
        "as_of_date": asof.isoformat(),
    })
    result = run_ready_dataset(dataset, asof_date=asof, analyze_security=analyze_security)

    if result.manifest.output_schema_version != ONEIL_OUTPUT_SCHEMA:
        raise ValueError("frozen morphology output schema drift")
    if result.manifest.engine_version != ONEIL_ENGINE_VERSION:
        raise ValueError("frozen morphology engine drift")

    output_hash = hashlib.sha256(result.jsonl.encode("utf-8")).hexdigest()
    lineage = CheckpointLineage(
        stage=CheckpointStage.RAW_ONEIL_MORPHOLOGY,
        source_identity=f"ussy-oneil-patterns@{FROZEN_ONEIL_SHA}",
        source_hash=output_hash,
        schema_version=ONEIL_OUTPUT_SCHEMA,
        contract_version=MORPHOLOGY_ADAPTER_VERSION,
        producer_commit=producer_commit,
        producer_run=producer_run,
        created_at=datetime.now(timezone.utc),
    )
    payload = asdict(lineage)
    payload["stage"] = lineage.stage.value
    payload["created_at"] = lineage.created_at.isoformat()
    payload["upstream_frozen_ready"] = {
        "source_identity": frozen_ready["source_identity"],
        "source_hash": frozen_ready["source_hash"],
        "as_of_date": asof.isoformat(),
    }
    payload["morphology"] = {
        "frozen_repo_sha": FROZEN_ONEIL_SHA,
        "engine_version": result.manifest.engine_version,
        "output_schema_version": result.manifest.output_schema_version,
        "record_count": result.manifest.record_count,
        "jsonl_sha256": output_hash,
    }
    return payload, result.jsonl
