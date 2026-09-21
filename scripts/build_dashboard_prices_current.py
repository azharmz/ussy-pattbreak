"""Build compact dashboard prices from current READY and current candidates."""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path
import boto3, pandas as pd
def sha(b): return "sha256:"+hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",default="checkpoints/dashboard-prices.jsonl"); a=ap.parse_args()
 s=boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto"); bucket=os.environ["R2_BUCKET_NAME"]
 ready=json.loads(s.get_object(Bucket=bucket,Key="production/ready/current.json")["Body"].read()); parquet_key=ready.get("parquet_key") or ready.get("ready",{}).get("parquet_key")
 if not parquet_key: raise ValueError("current READY pointer missing parquet_key")
 raw=s.get_object(Bucket=bucket,Key=parquet_key)["Body"].read(); ready_hash=sha(raw); expected=ready.get("source_hash") or ready.get("parquet_sha256") or ready.get("ready",{}).get("source_hash")
 if expected and str(expected).replace("sha256:","")!=ready_hash.replace("sha256:",""): raise ValueError("current READY parquet checksum mismatch")
 cp=json.loads(s.get_object(Bucket=bucket,Key="pattern-breakout/production/candidates/current.json")["Body"].read()); candidates=s.get_object(Bucket=bucket,Key=cp["jsonl_key"])["Body"].read()
 if sha(candidates)!=cp["source_hash"]: raise ValueError("candidate checkpoint checksum mismatch")
 ids={str(json.loads(x)["security_id"]) for x in candidates.decode().splitlines() if x.strip()}; tmp=Path("current-ready.parquet"); tmp.write_bytes(raw)
 df=pd.read_parquet(tmp,columns=["date","security_id","ticker","close"]); df["security_id"]=df["security_id"].astype(str); df=df[df["security_id"].isin(ids)]; df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize(); cur=df.sort_values(["security_id","date"]).groupby("security_id",sort=False).tail(1)
 rows=[{"security_id":str(x.security_id),"ticker":str(x.ticker),"as_of_date":x.date.date().isoformat(),"close":float(x.close)} for x in cur.itertuples()]
 if not rows: raise ValueError("no candidate prices in current READY")
 asof=max(x["as_of_date"] for x in rows); rows=[x for x in rows if x["as_of_date"]==asof]; out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); body="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in sorted(rows,key=lambda x:x["security_id"])); out.write_text(body)
 meta={"schema_version":"dashboard-price-enrichment-v2","as_of_date":asof,"record_count":len(rows),"candidate_security_count":len(ids),"missing_security_count":len(ids)-len(rows),"source_hash":sha(body.encode()),"ready_source_hash":ready_hash,"ready_parquet_key":parquet_key,"candidate_source_hash":cp["source_hash"]}; out.with_suffix(".json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n"); print(json.dumps(meta,sort_keys=True))
if __name__=="__main__": main()
