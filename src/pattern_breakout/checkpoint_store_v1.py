"""Generic durable R2 checkpoint store for immutable production stage outputs."""
from __future__ import annotations
import gzip, hashlib, json
from datetime import datetime, timezone

ALLOWED_STAGES={"morphology","candidates","t1-execution","dashboard-opportunities"}
MORPHOLOGY_REPRESENTATION="ndjson+gzip"
MORPHOLOGY_COMPRESSION_LEVEL=6

def _prefix(stage:str)->str:
    if stage not in ALLOWED_STAGES: raise ValueError(f"unsupported durable stage: {stage}")
    return f"pattern-breakout/production/{stage}"

def _sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def _gzip_deterministic(raw:bytes)->bytes: return gzip.compress(raw,compresslevel=MORPHOLOGY_COMPRESSION_LEVEL,mtime=0)

def publish_checkpoint(s3,bucket:str,*,stage:str,as_of_date:str,metadata:dict,jsonl:bytes)->dict:
    digest=_sha(jsonl); expected=metadata.get("source_hash")
    if expected not in {digest,f"sha256:{digest}"}: raise ValueError(f"{stage} payload hash mismatch")
    prefix=_prefix(stage); metadata=dict(metadata)
    if stage=="morphology":
        stored=_gzip_deterministic(jsonl); stored_digest=_sha(stored)
        key=f"{prefix}/runs/{as_of_date}/{digest}.jsonl.gz"
        metadata["storage"]={"representation":MORPHOLOGY_REPRESENTATION,"compression":{"codec":"gzip","level":MORPHOLOGY_COMPRESSION_LEVEL,"mtime":0},"logical_sha256":digest,"logical_bytes":len(jsonl),"stored_sha256":stored_digest,"stored_bytes":len(stored),"compression_ratio":len(stored)/len(jsonl),"semantic_verification":"sha256-byte-exact-after-decompress"}
        body=stored; content_encoding="gzip"
    else:
        key=f"{prefix}/runs/{as_of_date}/{digest}.jsonl"; body=jsonl; content_encoding=None
    mkey=f"{prefix}/runs/{as_of_date}/{digest}.json"
    canonical=(json.dumps(metadata,sort_keys=True,separators=(",",":"))+"\n").encode()
    kwargs={"Bucket":bucket,"Key":key,"Body":body,"ContentType":"application/x-ndjson"}
    if content_encoding: kwargs["ContentEncoding"]=content_encoding
    s3.put_object(**kwargs)
    s3.put_object(Bucket=bucket,Key=mkey,Body=canonical,ContentType="application/json")
    pointer={"schema_version":"pattern-breakout-checkpoint-pointer-v2" if stage=="morphology" else "pattern-breakout-checkpoint-pointer-v1","stage":stage,"as_of_date":as_of_date,"source_hash":f"sha256:{digest}","jsonl_key":key,"metadata_key":mkey,"updated_at":datetime.now(timezone.utc).isoformat()}
    if stage=="morphology": pointer.update({"representation":MORPHOLOGY_REPRESENTATION,"stored_hash":f"sha256:{metadata['storage']['stored_sha256']}","stored_bytes":metadata["storage"]["stored_bytes"],"logical_bytes":metadata["storage"]["logical_bytes"]})
    s3.put_object(Bucket=bucket,Key=f"{prefix}/current.json",Body=(json.dumps(pointer,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
    return pointer

def load_current_checkpoint(s3,bucket:str,*,stage:str):
    prefix=_prefix(stage); pointer=json.loads(s3.get_object(Bucket=bucket,Key=f"{prefix}/current.json")["Body"].read())
    if pointer.get("stage")!=stage: raise ValueError("durable checkpoint stage mismatch")
    stored=s3.get_object(Bucket=bucket,Key=pointer["jsonl_key"])["Body"].read()
    metadata=json.loads(s3.get_object(Bucket=bucket,Key=pointer["metadata_key"])["Body"].read())
    representation=pointer.get("representation","ndjson")
    if representation==MORPHOLOGY_REPRESENTATION:
        sh=_sha(stored); storage=metadata.get("storage") or {}
        if pointer.get("stored_hash")!=f"sha256:{sh}": raise ValueError("durable checkpoint stored checksum mismatch")
        if storage.get("stored_sha256")!=sh or storage.get("stored_bytes")!=len(stored): raise ValueError("durable checkpoint stored metadata mismatch")
        try: raw=gzip.decompress(stored)
        except Exception as exc: raise ValueError("durable checkpoint gzip decompression failed") from exc
        if storage.get("logical_bytes")!=len(raw): raise ValueError("durable checkpoint logical size mismatch")
    elif representation=="ndjson": raw=stored
    else: raise ValueError("unsupported durable checkpoint representation")
    digest=_sha(raw)
    if pointer.get("source_hash")!=f"sha256:{digest}": raise ValueError("durable checkpoint checksum mismatch")
    mh=metadata.get("source_hash")
    if mh not in {digest,f"sha256:{digest}"}: raise ValueError("durable checkpoint metadata mismatch")
    if representation==MORPHOLOGY_REPRESENTATION and metadata["storage"].get("logical_sha256")!=digest: raise ValueError("durable checkpoint logical metadata mismatch")
    return pointer,metadata,raw
