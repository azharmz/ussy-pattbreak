"""Publish an existing verified stage checkpoint to durable R2."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import boto3
from pattern_breakout.checkpoint_store_v1 import publish_checkpoint

FILES={
 "morphology":("raw-oneil-morphology.json","raw-oneil-morphology.jsonl"),
 "candidates":("breakout-candidate.json","breakout-candidate.jsonl"),
 "t1-execution":("t1-execution.json","t1-execution.jsonl"),
 "dashboard-opportunities":("dashboard-opportunities.json","dashboard-opportunities.jsonl"),
 "dashboard-prices":("dashboard-prices.json","dashboard-prices.jsonl"),
}

def client():
 return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--stage",choices=sorted(FILES),required=True); ap.add_argument("--dir",default="checkpoints"); a=ap.parse_args()
 meta_name,data_name=FILES[a.stage]; root=Path(a.dir)
 meta=json.loads((root/meta_name).read_text()); raw=(root/data_name).read_bytes()
 if a.stage=="morphology":
  source_hash="sha256:"+meta["morphology"]["jsonl_sha256"]; meta=dict(meta); meta["source_hash"]=source_hash
  asof=meta["upstream_frozen_ready"]["as_of_date"]
 elif a.stage=="candidates":
  asof=meta["upstream"]["as_of_date"]
 elif a.stage=="t1-execution":
  asof=meta["execution_ready"]["as_of_date"]
 else:
  asof=meta["as_of_date"]
 p=publish_checkpoint(client(),os.environ["R2_BUCKET_NAME"],stage=a.stage,as_of_date=asof,metadata=meta,jsonl=raw)
 print(json.dumps(p,sort_keys=True))
if __name__=="__main__": main()
