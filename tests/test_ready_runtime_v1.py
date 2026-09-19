import hashlib
import io
import json
import pytest

from pattern_breakout.ready_runtime_v1 import read_and_freeze_ready


BODY = b"parquet-test-body"
SHA = hashlib.sha256(BODY).hexdigest()


def manifest(sha=SHA):
    return {
        "schema_version": 2,
        "created_at": "2026-09-19T01:00:00+00:00",
        "as_of_date": "2026-09-18",
        "terminal_date_max": "2026-09-18",
        "parquet_key": "production/ready/runs/2026-09-18.parquet",
        "sha256": sha,
        "securities": 1,
        "rows": 250,
        "security_ids": ["sec-a"],
    }


class FakeS3:
    def __init__(self, pointer_versions=None, body=BODY):
        self.pointer_versions = pointer_versions or [manifest()]
        self.body = body
        self.pointer_reads = 0
        self.calls = []

    def get_object(self, *, Bucket, Key):
        self.calls.append(("get_object", Bucket, Key))
        if Key == "production/ready/current.json":
            idx = min(self.pointer_reads, len(self.pointer_versions) - 1)
            self.pointer_reads += 1
            raw = json.dumps(self.pointer_versions[idx], sort_keys=True).encode()
            return {"Body": io.BytesIO(raw)}
        return {"Body": io.BytesIO(self.body)}


def test_readonly_runtime_verifies_body_and_emits_checkpoint():
    s3 = FakeS3()
    payload, body = read_and_freeze_ready(
        s3, "ussy-data", producer_commit="abc", producer_run="123")
    assert body == BODY
    assert payload["stage"] == "frozen_ready"
    assert payload["source_hash"] == f"sha256:{SHA}"
    assert payload["ready"]["rows"] == 250
    assert all(call[0] == "get_object" for call in s3.calls)


def test_checksum_mismatch_fails_closed():
    with pytest.raises(ValueError, match="checksum"):
        read_and_freeze_ready(
            FakeS3(body=b"changed"), "ussy-data",
            producer_commit="abc", producer_run="123")


def test_pointer_change_during_freeze_fails_closed():
    second = manifest()
    second["as_of_date"] = second["terminal_date_max"] = "2026-09-19"
    second["parquet_key"] = "production/ready/runs/2026-09-19.parquet"
    with pytest.raises(RuntimeError, match="pointer changed"):
        read_and_freeze_ready(
            FakeS3(pointer_versions=[manifest(), second]), "ussy-data",
            producer_commit="abc", producer_run="123")
