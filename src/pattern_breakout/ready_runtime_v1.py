"""Thin read-only R2 runtime for producing a durable FROZEN_READY checkpoint."""
from __future__ import annotations
import hashlib
import json
from dataclasses import asdict
from typing import Any

from .ready_adapter_v1 import freeze_ready_manifest


READY_POINTER_KEY = "production/ready/current.json"


def read_and_freeze_ready(
    s3: Any,
    bucket: str,
    *,
    producer_commit: str,
    producer_run: str,
) -> tuple[dict, bytes]:
    """Read pointer + immutable Parquet, verify checksum, and return checkpoint payload.

    The caller owns persistence of the returned JSON-serializable checkpoint.
    No write method is called on the supplied R2 client.
    """
    pointer_raw = s3.get_object(Bucket=bucket, Key=READY_POINTER_KEY)["Body"].read()
    manifest = json.loads(pointer_raw)
    lineage = freeze_ready_manifest(
        manifest, producer_commit=producer_commit, producer_run=producer_run)

    parquet_key = manifest["parquet_key"]
    body = s3.get_object(Bucket=bucket, Key=parquet_key)["Body"].read()
    digest = hashlib.sha256(body).hexdigest()
    expected = manifest["sha256"].lower()
    if digest != expected:
        raise ValueError("READY Parquet checksum mismatch")

    # Re-read pointer after immutable-object verification. If producer advanced
    # current.json during this read, fail closed rather than freezing mixed lineage.
    pointer_after = s3.get_object(Bucket=bucket, Key=READY_POINTER_KEY)["Body"].read()
    if pointer_after != pointer_raw:
        raise RuntimeError("READY pointer changed during freeze; retry")

    payload = asdict(lineage)
    payload["stage"] = lineage.stage.value
    payload["created_at"] = lineage.created_at.isoformat()
    payload["ready"] = {
        "pointer_key": READY_POINTER_KEY,
        "parquet_key": parquet_key,
        "as_of_date": manifest["as_of_date"],
        "securities": manifest["securities"],
        "rows": manifest.get("rows"),
    }
    return payload, body
