"""Publish a PIT opportunity research snapshot to durable R2.

Research-only. This never updates dashboard/D1 or an Opportunity current pointer.
"""
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
import boto3

PREFIX="pattern-breakout/research/opportunity-cohorts"

def client():
 return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--snapshot",default="checkpoints/dashboard-opportunities.jsonl"); ap.add_argument("--metadata",default="checkpoints/dashboard-opportunities.json"); a=ap.parse_args()
 p=Path(a.snapshot); m=json.loads(Path(a.metadata).read_text()); raw=p.read_bytes(); h=hashlib.sha256(raw).hexdigest(); day=m["as_of_date"]
 if m.get("source_hash","").removeprefix("sha256:")!=h: raise ValueError("snapshot metadata checksum mismatch")
 manifest={"stage":"opportunity-research-cohort","status":"RESEARCH_ONLY","as_of_date":day,
   "source_hash":"sha256:"+h,"schema_version":m.get("schema_version"),
   "record_count":m.get("record_count"),"methodology_change":False,
   "eligibility_rule_defined":False,
   "jsonl_key":f"{PREFIX}/by-as-of/{day}/{h}.jsonl"}
 body=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode()
 s=client(); b=os.environ["R2_BUCKET_NAME"]
 s.put_object(Bucket=b,Key=manifest["jsonl_key"],Body=raw,ContentType="application/x-ndjson")
 s.put_object(Bucket=b,Key=f"{PREFIX}/by-as-of/{day}/{h}.json",Body=body,ContentType="application/json")
 s.put_object(Bucket=b,Key=f"{PREFIX}/by-as-of/{day}/index.json",Body=body,ContentType="application/json")
 print(json.dumps(manifest,sort_keys=True))
if __name__=="__main__": main()
