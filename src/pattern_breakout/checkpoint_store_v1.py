"""Generic durable R2 checkpoint store for immutable production stage outputs."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone

ALLOWED_STAGES={"morphology","candidates","t1-execution"}

def _prefix(stage:str)->str:
    if stage not in ALLOWED_STAGES: raise ValueError(f"unsupported durable stage: {stage}")
    return f"pattern-breakout/production/{stage}"

def publish_checkpoint(s3,bucket:str,*,stage:str,as_of_date:str,metadata:dict,jsonl:bytes)->dict:
    digest=hashlib.sha256(jsonl).hexdigest()
    expected=metadata.get("source_hash")
    if expected not in {digest,f"sha256:{digest}"}:
        raise ValueError(f"{stage} payload hash mismatch")
    prefix=_prefix(stage); key=f"{prefix}/runs/{as_of_date}/{digest}.jsonl"; mkey=f"{prefix}/runs/{as_of_date}/{digest}.json"
    canonical=(json.dumps(metadata,sort_keys=True,separators=(",",":"))+"\n").encode()
    s3.put_object(Bucket=bucket,Key=key,Body=jsonl,ContentType="application/x-ndjson")
    s3.put_object(Bucket=bucket,Key=mkey,Body=canonical,ContentType="application/json")
    pointer={"schema_version":"pattern-breakout-checkpoint-pointer-v1","stage":stage,"as_of_date":as_of_date,"source_hash":f"sha256:{digest}","jsonl_key":key,"metadata_key":mkey,"updated_at":datetime.now(timezone.utc).isoformat()}
    s3.put_object(Bucket=bucket,Key=f"{prefix}/current.json",Body=(json.dumps(pointer,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
    return pointer

def load_current_checkpoint(s3,bucket:str,*,stage:str):
    prefix=_prefix(stage)
    pointer=json.loads(s3.get_object(Bucket=bucket,Key=f"{prefix}/current.json")["Body"].read())
    if pointer.get("stage")!=stage: raise ValueError("durable checkpoint stage mismatch")
    raw=s3.get_object(Bucket=bucket,Key=pointer["jsonl_key"])["Body"].read()
    metadata=json.loads(s3.get_object(Bucket=bucket,Key=pointer["metadata_key"])["Body"].read())
    digest=hashlib.sha256(raw).hexdigest()
    if pointer.get("source_hash")!=f"sha256:{digest}": raise ValueError("durable checkpoint checksum mismatch")
    mh=metadata.get("source_hash")
    if mh not in {digest,f"sha256:{digest}"}: raise ValueError("durable checkpoint metadata mismatch")
    return pointer,metadata,raw
