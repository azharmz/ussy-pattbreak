import pytest

from pattern_breakout.ready_adapter_v1 import (
    READY_SCHEMA_VERSION, freeze_ready_manifest,
)
from pattern_breakout.pipeline_v1 import CheckpointStage, PIPELINE_CONTRACT_VERSION


SHA = "a" * 64


def manifest(**overrides):
    x = {
        "schema_version": 2,
        "created_at": "2026-09-19T01:00:00+00:00",
        "as_of_date": "2026-09-18",
        "terminal_date_max": "2026-09-18",
        "parquet_key": "production/ready/runs/2026-09-18.parquet",
        "sha256": SHA,
        "securities": 2,
        "security_ids": ["sec-a", "sec-b"],
    }
    x.update(overrides)
    return x


def test_freezes_exact_pointer_object_and_hash():
    x = freeze_ready_manifest(
        manifest(), producer_commit="abc123", producer_run="github-actions:7")
    assert x.stage == CheckpointStage.FROZEN_READY
    assert x.source_identity.endswith(
        "production/ready/current.json->production/ready/runs/2026-09-18.parquet")
    assert x.source_hash == f"sha256:{SHA}"
    assert x.schema_version == READY_SCHEMA_VERSION
    assert x.contract_version == PIPELINE_CONTRACT_VERSION


@pytest.mark.parametrize("patch", [
    {"schema_version": 1},
    {"parquet_key": "production/rolling/latest.parquet"},
    {"sha256": "bad"},
    {"terminal_date_max": "2026-09-17"},
    {"security_ids": []},
    {"securities": 3},
    {"security_ids": ["sec-a", "sec-a"]},
    {"created_at": "2026-09-19T01:00:00"},
])
def test_invalid_or_mutable_ready_identity_fails_closed(patch):
    with pytest.raises(ValueError):
        freeze_ready_manifest(
            manifest(**patch), producer_commit="abc123",
            producer_run="github-actions:7")
