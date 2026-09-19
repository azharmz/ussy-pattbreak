"""CLI: freeze canonical READY and produce durable raw frozen morphology."""
from __future__ import annotations
import json
import os
from pathlib import Path

from pattern_breakout.frozen_morphology_adapter_v1 import run_frozen_morphology
from pattern_breakout.ready_runtime_v1 import read_and_freeze_ready


def make_readonly_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def main():
    out = Path("checkpoints")
    out.mkdir(parents=True, exist_ok=True)
    s3 = make_readonly_client()
    frozen_ready, parquet_body = read_and_freeze_ready(
        s3, os.environ["R2_BUCKET_NAME"],
        producer_commit=os.environ["GITHUB_SHA"],
        producer_run=os.environ.get("GITHUB_RUN_ID", "local"),
    )
    (out / "frozen-ready.json").write_text(
        json.dumps(frozen_ready, indent=2, sort_keys=True) + "\n")

    morphology, jsonl = run_frozen_morphology(
        parquet_body=parquet_body,
        frozen_ready=frozen_ready,
        producer_commit=os.environ["GITHUB_SHA"],
        producer_run=os.environ.get("GITHUB_RUN_ID", "local"),
    )
    (out / "raw-oneil-morphology.json").write_text(
        json.dumps(morphology, indent=2, sort_keys=True) + "\n")
    (out / "raw-oneil-morphology.jsonl").write_text(jsonl)
    print(json.dumps(morphology["morphology"], sort_keys=True))


if __name__ == "__main__":
    main()
