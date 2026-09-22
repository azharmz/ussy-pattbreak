"""Durable, isolated v2 checkpoint namespaces. Never writes v1 pointers."""
import hashlib,json
from datetime import datetime,timezone
PREFIXES={"breakout-events-v2":"pattern-breakout/production/breakout-events-v2","t1-event-execution-v2":"pattern-breakout/production/t1-event-execution-v2"}
def publish_v2(s3,bucket,*,stage,signal_date,metadata,jsonl):
 if stage not in PREFIXES:raise ValueError("unsupported v2 stage")
 d=hashlib.sha256(jsonl).hexdigest()
 if metadata.get("source_hash") not in {d,"sha256:"+d}:raise ValueError("v2 payload hash mismatch")
 p=PREFIXES[stage];key=f"{p}/runs/{signal_date}/{d}.jsonl";mkey=f"{p}/runs/{signal_date}/{d}.json"
 s3.put_object(Bucket=bucket,Key=key,Body=jsonl,ContentType="application/x-ndjson");s3.put_object(Bucket=bucket,Key=mkey,Body=(json.dumps(metadata,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
 ptr={"schema_version":"pattern-breakout-v2-pointer-v1","stage":stage,"signal_date":signal_date,"source_hash":"sha256:"+d,"jsonl_key":key,"metadata_key":mkey,"updated_at":datetime.now(timezone.utc).isoformat()}
 s3.put_object(Bucket=bucket,Key=f"{p}/by-signal-date/{signal_date}.json",Body=(json.dumps(ptr,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
 return ptr
