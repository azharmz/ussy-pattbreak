"""Freeze an already-validated ussy-data READY manifest into pipeline lineage.

This adapter is deliberately storage-agnostic. The caller reads the private R2
pointer/object; this module validates immutable READY identity and emits the
FROZEN_READY checkpoint metadata used by downstream stages.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping

from .pipeline_v1 import (
    CheckpointLineage, CheckpointStage, PIPELINE_CONTRACT_VERSION,
)

READY_POINTER_IDENTITY = "ussy-data:production/ready/current.json"
READY_SCHEMA_VERSION = "ussy-data-ready-v2"


def freeze_ready_manifest(
    manifest: Mapping[str, Any],
    *,
    producer_commit: str,
    producer_run: str,
) -> CheckpointLineage:
    if manifest.get("schema_version") != 2:
        raise ValueError("READY schema_version must be 2")

    parquet_key = manifest.get("parquet_key")
    sha256 = manifest.get("sha256")
    as_of = manifest.get("as_of_date")
    terminal_max = manifest.get("terminal_date_max")
    security_ids = manifest.get("security_ids")
    securities = manifest.get("securities")

    if not isinstance(parquet_key, str) or not parquet_key.startswith("production/ready/runs/"):
        raise ValueError("READY parquet_key is not immutable run storage")
    if not isinstance(sha256, str) or len(sha256) != 64:
        raise ValueError("READY sha256 is invalid")
    try:
        int(sha256, 16)
    except ValueError as exc:
        raise ValueError("READY sha256 is invalid") from exc
    if not isinstance(as_of, str) or not as_of or terminal_max != as_of:
        raise ValueError("READY as-of/terminal-date invariant failed")
    if not isinstance(security_ids, list) or not security_ids:
        raise ValueError("READY security_ids missing")
    if len(security_ids) != len(set(security_ids)) or securities != len(security_ids):
        raise ValueError("READY security count/identity mismatch")

    created_raw = manifest.get("created_at")
    if not isinstance(created_raw, str):
        raise ValueError("READY created_at missing")
    created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
    if created_at.tzinfo is None:
        raise ValueError("READY created_at must be timezone-aware")

    # Identity freezes both the pointer contract and exact immutable object key.
    source_identity = f"{READY_POINTER_IDENTITY}->{parquet_key}"
    return CheckpointLineage(
        stage=CheckpointStage.FROZEN_READY,
        source_identity=source_identity,
        source_hash=f"sha256:{sha256.lower()}",
        schema_version=READY_SCHEMA_VERSION,
        contract_version=PIPELINE_CONTRACT_VERSION,
        producer_commit=producer_commit,
        producer_run=producer_run,
        created_at=created_at,
    )
