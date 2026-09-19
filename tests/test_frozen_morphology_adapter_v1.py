import hashlib
import io
import pandas as pd
import pytest

from pattern_breakout.frozen_morphology_adapter_v1 import ready_v2_frame


def parquet_bytes():
    frame = pd.DataFrame([{
        "date": "2026-09-18", "security_id": "s1", "ticker": "XYZ",
        "open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0,
        "adj_close": 101.0, "volume": 1_000_000,
    }])
    buf = io.BytesIO()
    frame.to_parquet(buf, index=False)
    return buf.getvalue()


def checkpoint(body):
    return {
        "stage": "frozen_ready",
        "schema_version": "ussy-data-ready-v2",
        "source_hash": hashlib.sha256(body).hexdigest(),
    }


def test_verified_ready_v2_bytes_materialize():
    body = parquet_bytes()
    frame = ready_v2_frame(body, checkpoint(body))
    assert list(frame["ticker"]) == ["XYZ"]


def test_hash_mismatch_fails_closed():
    body = parquet_bytes()
    cp = checkpoint(body)
    cp["source_hash"] = "0" * 64
    with pytest.raises(ValueError, match="source_hash"):
        ready_v2_frame(body, cp)


def test_wrong_ready_schema_fails_closed():
    body = parquet_bytes()
    cp = checkpoint(body)
    cp["schema_version"] = "ussy-data-ready-v1"
    with pytest.raises(ValueError, match="schema"):
        ready_v2_frame(body, cp)
