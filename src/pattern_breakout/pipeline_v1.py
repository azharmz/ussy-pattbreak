"""Durable checkpoint lineage contract for Pattern Breakout pipeline v1."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping


PIPELINE_CONTRACT_VERSION = "pattern-breakout-pipeline-v1"


class CheckpointStage(str, Enum):
    FROZEN_READY = "frozen_ready"
    RAW_ONEIL_MORPHOLOGY = "raw_oneil_morphology"
    BREAKOUT_CANDIDATE = "breakout_candidate"
    T1_EXECUTION = "t1_execution"
    LIFECYCLE = "lifecycle"


@dataclass(frozen=True)
class CheckpointLineage:
    stage: CheckpointStage
    source_identity: str
    source_hash: str
    schema_version: str
    contract_version: str
    producer_commit: str
    producer_run: str
    created_at: datetime


def validate_checkpoint_lineage(
    lineage: CheckpointLineage,
    *,
    expected_stage: CheckpointStage,
    expected_source_identity: str,
    expected_source_hash: str,
    expected_schema_version: str,
    expected_contract_version: str,
) -> None:
    """Fail closed when a durable checkpoint cannot prove exact lineage."""
    expected: Mapping[str, object] = {
        "stage": expected_stage,
        "source_identity": expected_source_identity,
        "source_hash": expected_source_hash,
        "schema_version": expected_schema_version,
        "contract_version": expected_contract_version,
    }
    actual: Mapping[str, object] = {
        "stage": lineage.stage,
        "source_identity": lineage.source_identity,
        "source_hash": lineage.source_hash,
        "schema_version": lineage.schema_version,
        "contract_version": lineage.contract_version,
    }
    mismatches = [k for k in expected if actual[k] != expected[k]]
    missing = [
        name for name, value in {
            "source_identity": lineage.source_identity,
            "source_hash": lineage.source_hash,
            "schema_version": lineage.schema_version,
            "contract_version": lineage.contract_version,
            "producer_commit": lineage.producer_commit,
            "producer_run": lineage.producer_run,
        }.items() if not str(value).strip()
    ]
    if lineage.created_at.tzinfo is None:
        missing.append("created_at_timezone")
    if mismatches or missing:
        raise ValueError(
            "checkpoint lineage rejected: "
            f"mismatches={sorted(mismatches)} missing={sorted(missing)}"
        )
