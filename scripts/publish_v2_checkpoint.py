"""Publish isolated v2 checkpoints without advancing v1 production pointers."""
import argparse,json,os
from pathlib import Path
import boto3
from pattern_breakout.checkpoint_store_v2 import publish_v2
FILES={"breakout-events-v2":("breakout-events-v2.json","breakout-events-v2.jsonl"),"t1-event-execution-v2":("t1-event-execution-v2.json","t1-event-execution-v2.jsonl"),"security-execution-v2":("security-execution-v2.json","security-execution-v2.jsonl"),"lifecycle-v2":("lifecycle-v2.json","lifecycle-v2.jsonl")}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--stage",choices=sorted(FILES),required=True);ap.add_argument("--dir",default="checkpoints");a=ap.parse_args()
 mn,dn=FILES[a.stage];root=Path(a.dir);m=json.loads((root/mn).read_text());raw=(root/dn).read_bytes()
 s=boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
 print(json.dumps(publish_v2(s,os.environ["R2_BUCKET_NAME"],stage=a.stage,signal_date=m["signal_date"],metadata=m,jsonl=raw),sort_keys=True))
if __name__=="__main__":main()
