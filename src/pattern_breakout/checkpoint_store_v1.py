"""Generic durable R2 checkpoint store for immutable production stage outputs."""
from __future__ import annotations
import gzip, hashlib, json
from datetime import datetime, timezone

ALLOWED_STAGES={"morphology","candidates","t1-execution","dashboard-opportunities"}
MORPHOLOGY_REPRESENTATION="ndjson+gzip"
MORPHOLOGY_COMPRESSION_LEVEL=6
MORPHOLOGY_RETENTION_DATES=2
COMPRESSED_STAGES={"morphology","dashboard-opportunities"}
RETENTION_STAGES={"morphology","dashboard-opportunities"}

def _prefix(stage:str)->str:
    if stage not in ALLOWED_STAGES: raise ValueError(f"unsupported durable stage: {stage}")
    return f"pattern-breakout/production/{stage}"

def _sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def _gzip_deterministic(raw:bytes)->bytes: return gzip.compress(raw,compresslevel=MORPHOLOGY_COMPRESSION_LEVEL,mtime=0)

def _delete_prefix(s3,bucket:str,prefix:str)->int:
    deleted=0; token=None
    while True:
        kwargs={"Bucket":bucket,"Prefix":prefix}
        if token: kwargs["ContinuationToken"]=token
        page=s3.list_objects_v2(**kwargs)
        objects=[{"Key":x["Key"]} for x in page.get("Contents",[])]
        if objects:
            s3.delete_objects(Bucket=bucket,Delete={"Objects":objects,"Quiet":True}); deleted+=len(objects)
        if not page.get("IsTruncated"): break
        token=page["NextContinuationToken"]
    return deleted

def enforce_stage_retention(s3,bucket:str,stage:str,current_pointer:dict,keep_dates:int=2)->dict:
    """Keep current + previous dates for reconstructable large derived stages."""
    if stage not in RETENTION_STAGES: raise ValueError("stage has no automatic retention policy")
    if keep_dates<2: raise ValueError(f"{stage} retention must preserve current plus rollback date")
    prefix=_prefix(stage); current_date=current_pointer["as_of_date"]
    dates=set(); token=None
    while True:
        kwargs={"Bucket":bucket,"Prefix":prefix+"/runs/"}
        if token: kwargs["ContinuationToken"]=token
        page=s3.list_objects_v2(**kwargs)
        for x in page.get("Contents",[]):
            rest=x["Key"][len(prefix+"/runs/"):]
            if "/" in rest: dates.add(rest.split("/",1)[0])
        if not page.get("IsTruncated"): break
        token=page["NextContinuationToken"]
    keep=set(sorted(dates,reverse=True)[:keep_dates])
    if current_date not in keep: raise ValueError(f"current {stage} date would fall outside retention window")
    removed={}
    for d in sorted(dates-keep):
        removed[d]=_delete_prefix(s3,bucket,f"{prefix}/runs/{d}/")
    return {"policy":"2-dates-1-logical-snapshot-per-date","stage":stage,"keep_dates":sorted(keep,reverse=True),"removed":removed}

def publish_checkpoint(s3,bucket:str,*,stage:str,as_of_date:str,metadata:dict,jsonl:bytes)->dict:
    digest=_sha(jsonl); expected=metadata.get("source_hash")
    if expected not in {digest,f"sha256:{digest}"}: raise ValueError(f"{stage} payload hash mismatch")
    prefix=_prefix(stage); metadata=dict(metadata)
    if stage in COMPRESSED_STAGES:
        stored=_gzip_deterministic(jsonl); stored_digest=_sha(stored)
        key=f"{prefix}/runs/{as_of_date}/{digest}.jsonl.gz"
        metadata["storage"]={"representation":MORPHOLOGY_REPRESENTATION,"compression":{"codec":"gzip","level":MORPHOLOGY_COMPRESSION_LEVEL,"mtime":0},"logical_sha256":digest,"logical_bytes":len(jsonl),"stored_sha256":stored_digest,"stored_bytes":len(stored),"compression_ratio":len(stored)/len(jsonl),"semantic_verification":"sha256-byte-exact-after-decompress"}
        body=stored; content_encoding="gzip"
    else:
        key=f"{prefix}/runs/{as_of_date}/{digest}.jsonl"; body=jsonl; content_encoding=None
    mkey=f"{prefix}/runs/{as_of_date}/{digest}.storage-v2.json" if stage in COMPRESSED_STAGES else f"{prefix}/runs/{as_of_date}/{digest}.json"
    canonical=(json.dumps(metadata,sort_keys=True,separators=(",",":"))+"\n").encode()
    kwargs={"Bucket":bucket,"Key":key,"Body":body,"ContentType":"application/x-ndjson"}
    if content_encoding: kwargs["ContentEncoding"]=content_encoding
    s3.put_object(**kwargs)
    s3.put_object(Bucket=bucket,Key=mkey,Body=canonical,ContentType="application/json")
    pointer={"schema_version":"pattern-breakout-checkpoint-pointer-v2" if stage in COMPRESSED_STAGES else "pattern-breakout-checkpoint-pointer-v1","stage":stage,"as_of_date":as_of_date,"source_hash":f"sha256:{digest}","jsonl_key":key,"metadata_key":mkey,"updated_at":datetime.now(timezone.utc).isoformat()}
    if stage in COMPRESSED_STAGES: pointer.update({"representation":MORPHOLOGY_REPRESENTATION,"stored_hash":f"sha256:{metadata['storage']['stored_sha256']}","stored_bytes":metadata["storage"]["stored_bytes"],"logical_bytes":metadata["storage"]["logical_bytes"]})
    s3.put_object(Bucket=bucket,Key=f"{prefix}/current.json",Body=(json.dumps(pointer,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
    if stage in RETENTION_STAGES:
        # Cleanup only after the new immutable payload, manifest and CURRENT pointer are durable.
        pointer["retention"]=enforce_stage_retention(s3,bucket,stage,pointer)
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
