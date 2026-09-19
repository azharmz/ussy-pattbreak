"""Advance the durable lifecycle checkpoint from R2 without GitHub run IDs."""
from __future__ import annotations
import os, tempfile
from pathlib import Path
import boto3
from pattern_breakout.lifecycle_store_v1 import load_current_lifecycle
from update_daily_lifecycle import main as update_main

def client():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
    s3=client(); bucket=os.environ["R2_BUCKET_NAME"]
    _,meta,raw=load_current_lifecycle(s3,bucket)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td); (p/"lifecycle.json").write_text(__import__("json").dumps(meta)); (p/"lifecycle.jsonl").write_bytes(raw)
        import sys
        old=sys.argv; sys.argv=["update_daily_lifecycle.py","--input-dir",td,"--output-dir","checkpoints"]
        try: update_main()
        finally: sys.argv=old
if __name__=="__main__": main()
