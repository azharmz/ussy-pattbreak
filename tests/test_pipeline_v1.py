from datetime import datetime, timezone
import pytest

from pattern_breakout.pipeline_v1 import (
    CheckpointLineage, CheckpointStage, PIPELINE_CONTRACT_VERSION,
    validate_checkpoint_lineage,
)


def lineage(**overrides):
    x = dict(
        stage=CheckpointStage.BREAKOUT_CANDIDATE,
        source_identity="ussy-data:production/ready/current.json",
        source_hash="sha256:abc",
        schema_version="oneil-pattern-output-v2",
        contract_version=PIPELINE_CONTRACT_VERSION,
        producer_commit="deadbeef",
        producer_run="github-actions:123",
        created_at=datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc),
    )
    x.update(overrides)
    return CheckpointLineage(**x)


def validate(x):
    validate_checkpoint_lineage(
        x,
        expected_stage=CheckpointStage.BREAKOUT_CANDIDATE,
        expected_source_identity="ussy-data:production/ready/current.json",
        expected_source_hash="sha256:abc",
        expected_schema_version="oneil-pattern-output-v2",
        expected_contract_version=PIPELINE_CONTRACT_VERSION,
    )


def test_exact_lineage_is_resumable():
    validate(lineage())


@pytest.mark.parametrize("field,value", [
    ("source_hash", "sha256:different"),
    ("source_identity", "other"),
    ("schema_version", "other"),
    ("contract_version", "other"),
    ("stage", CheckpointStage.LIFECYCLE),
])
def test_semantic_or_identity_mismatch_fails_closed(field, value):
    with pytest.raises(ValueError):
        validate(lineage(**{field: value}))


def test_missing_producer_identity_fails_closed():
    with pytest.raises(ValueError):
        validate(lineage(producer_commit=""))


def test_created_at_must_be_timezone_aware():
    with pytest.raises(ValueError):
        validate(lineage(created_at=datetime(2026, 9, 19, 1, 0)))
