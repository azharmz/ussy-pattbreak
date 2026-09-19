"""CLI: read canonical ussy-data READY and emit FROZEN_READY checkpoint JSON."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

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
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    s3 = make_readonly_client()
    bucket = os.environ["R2_BUCKET_NAME"]
    payload, _ = read_and_freeze_ready(
        s3, bucket,
        producer_commit=os.environ["GITHUB_SHA"],
        producer_run=os.environ.get("GITHUB_RUN_ID", "local"),
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["ready"], sort_keys=True))


if __name__ == "__main__":
    main()
