"""Durable R2 lifecycle checkpoint store with immutable objects and a stable current pointer."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone

PREFIX="pattern-breakout/production/lifecycle"
POINTER=f"{PREFIX}/current.json"

def publish_lifecycle_checkpoint(s3,bucket:str,*,metadata:dict,jsonl:bytes)->dict:
    digest=hashlib.sha256(jsonl).hexdigest()
    if metadata.get("source_hash") != f"sha256:{digest}": raise ValueError("lifecycle payload hash mismatch")
    asof=metadata["execution_ready"]["as_of_date"]
    key=f"{PREFIX}/runs/{asof}/{digest}.jsonl"; mkey=f"{PREFIX}/runs/{asof}/{digest}.json"
    # Immutable-by-content keys make retry idempotent.
    s3.put_object(Bucket=bucket,Key=key,Body=jsonl,ContentType="application/x-ndjson")
    s3.put_object(Bucket=bucket,Key=mkey,Body=(json.dumps(metadata,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
    pointer={"schema_version":"pattern-breakout-lifecycle-pointer-v1","as_of_date":asof,"source_hash":metadata["source_hash"],"jsonl_key":key,"metadata_key":mkey,"updated_at":datetime.now(timezone.utc).isoformat()}
    s3.put_object(Bucket=bucket,Key=POINTER,Body=(json.dumps(pointer,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
    return pointer

def load_current_lifecycle(s3,bucket:str):
    p=json.loads(s3.get_object(Bucket=bucket,Key=POINTER)["Body"].read())
    raw=s3.get_object(Bucket=bucket,Key=p["jsonl_key"])["Body"].read()
    meta=json.loads(s3.get_object(Bucket=bucket,Key=p["metadata_key"])["Body"].read())
    if hashlib.sha256(raw).hexdigest()!=p["source_hash"].removeprefix("sha256:"): raise ValueError("durable lifecycle checksum mismatch")
    if meta["source_hash"]!=p["source_hash"]: raise ValueError("durable lifecycle metadata mismatch")
    return p,meta,raw
