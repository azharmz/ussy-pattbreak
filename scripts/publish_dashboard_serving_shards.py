"""Publish additive small serving shards from the frozen dashboard-opportunities checkpoint.

This does not modify the canonical dashboard-opportunities storage contract or pointer.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, os
from datetime import datetime, timezone
import boto3
from pattern_breakout.checkpoint_store_v1 import load_current_checkpoint

PREFIX="pattern-breakout/production/dashboard-serving"
VERSION="dashboard-serving-shards-v1"

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def client():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--shard-rows",type=int,default=500); a=ap.parse_args()
    if not 100<=a.shard_rows<=2000: raise ValueError("shard-rows must be 100..2000")
    s3=client(); bucket=os.environ["R2_BUCKET_NAME"]
    pointer,meta,raw=load_current_checkpoint(s3,bucket,stage="dashboard-opportunities")
    lines=raw.splitlines(keepends=True)
    expected=meta.get("record_count")
    if expected is not None and len(lines)!=expected: raise ValueError("dashboard opportunity record count mismatch")
    source=pointer["source_hash"]; logical=source.replace("sha256:","")
    base=f"{PREFIX}/runs/{pointer['as_of_date']}/{logical}"
    shards=[]
    for n,start in enumerate(range(0,len(lines),a.shard_rows)):
        body=b"".join(lines[start:start+a.shard_rows])
        # Validate each logical line before publishing the transport shard.
        for line in body.splitlines(): json.loads(line)
        stored=gzip.compress(body,compresslevel=6,mtime=0)
        key=f"{base}/shards/{n:05d}.jsonl.gz"
        s3.put_object(Bucket=bucket,Key=key,Body=stored,ContentType="application/x-ndjson",ContentEncoding="gzip")
        shards.append({"index":n,"key":key,"record_count":len(lines[start:start+a.shard_rows]),"logical_sha256":sha(body),"stored_sha256":sha(stored),"logical_bytes":len(body),"stored_bytes":len(stored)})
    manifest={"schema_version":VERSION,"as_of_date":pointer["as_of_date"],"source_hash":source,"record_count":len(lines),"shard_rows":a.shard_rows,"shard_count":len(shards),"shards":shards,"created_at":datetime.now(timezone.utc).isoformat()}
    canonical=(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode(); manifest_hash=sha(canonical)
    mkey=f"{base}/manifest.json"
    s3.put_object(Bucket=bucket,Key=mkey,Body=canonical,ContentType="application/json")
    # Pointer promotion LAST; canonical checkpoint pointer remains untouched.
    serving={"schema_version":"dashboard-serving-pointer-v1","as_of_date":pointer["as_of_date"],"source_hash":source,"manifest_key":mkey,"manifest_hash":"sha256:"+manifest_hash,"record_count":len(lines),"shard_count":len(shards),"updated_at":datetime.now(timezone.utc).isoformat()}
    s3.put_object(Bucket=bucket,Key=f"{PREFIX}/current.json",Body=(json.dumps(serving,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
    print(json.dumps(serving,sort_keys=True))

if __name__=="__main__": main()
