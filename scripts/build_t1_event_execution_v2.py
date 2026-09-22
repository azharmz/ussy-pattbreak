"""Build v2 T+1 execution from an immutable breakout-event checkpoint."""
import argparse,hashlib,io,json,os
from dataclasses import asdict
from datetime import date,datetime,timezone
from pathlib import Path
import boto3,pandas as pd
from pattern_breakout.entry_v2 import decide_event_t1_open
from pattern_breakout.ready_runtime_v1 import read_and_freeze_ready
VERSION="pattern-breakout-t1-event-checkpoint-v2"
def client(): return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input-dir",default="upstream");ap.add_argument("--output-dir",default="checkpoints");a=ap.parse_args()
 inp=Path(a.input_dir);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 meta=json.loads((inp/"breakout-events-v2.json").read_text());raw=(inp/"breakout-events-v2.jsonl").read_bytes()
 if hashlib.sha256(raw).hexdigest()!=meta["source_hash"].removeprefix("sha256:"):raise ValueError("event checkpoint checksum mismatch")
 signal=date.fromisoformat(meta["signal_date"]); frozen,body=read_and_freeze_ready(client(),os.environ["R2_BUCKET_NAME"],producer_commit=os.getenv("GITHUB_SHA","local"),producer_run=os.getenv("GITHUB_RUN_ID","local"))
 asof=date.fromisoformat(frozen["ready"]["as_of_date"])
 if asof<=signal:raise ValueError("READY does not contain post-signal session")
 df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","open"]);df["date"]=pd.to_datetime(df["date"]).dt.date
 nb={}
 for sid,g in df[df.date>signal].sort_values(["security_id","date"]).groupby("security_id",sort=False):
  r=g.iloc[0];nb[str(sid)]=(r.date,float(r.open) if pd.notna(r.open) else None)
 rows=[];counts={}
 for line in raw.decode().splitlines():
  x=json.loads(line);n=nb.get(str(x["security_id"]))
  e=decide_event_t1_open(event_id=x["event_id"],security_id=x["security_id"],signal_date=date.fromisoformat(x["signal_date"]),pivot_level=x["pivot_level"],next_session_date=n[0] if n else None,next_open=n[1] if n else None)
  y=asdict(e)
  for k in ("signal_date","next_session_date","fill_date"):
   if y[k]:y[k]=y[k].isoformat()
  y["entry_state"]=y["entry_state"].value;y["supporting_assessment_ids"]=x["assessment_ids"];y["supporting_base_ids"]=x["base_ids"];y["supporting_lineage_ids"]=x["lineage_ids"];rows.append(y);counts[y["entry_state"]]=counts.get(y["entry_state"],0)+1
 payload="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows);digest=hashlib.sha256(payload.encode()).hexdigest()
 m={"stage":"t1-event-execution-v2","schema_version":"pattern-breakout-t1-event-v2","contract_version":VERSION,"signal_date":signal.isoformat(),"source_hash":"sha256:"+digest,"upstream_event_hash":meta["source_hash"],"execution_ready":{"source_hash":frozen["source_hash"],"as_of_date":frozen["ready"]["as_of_date"],"parquet_key":frozen["ready"]["parquet_key"]},"created_at":datetime.now(timezone.utc).isoformat(),"producer_commit":os.getenv("GITHUB_SHA","local"),"producer_run":os.getenv("GITHUB_RUN_ID","local"),"summary":{"event_count":len(rows),"state_counts":counts}}
 (out/"t1-event-execution-v2.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n");(out/"t1-event-execution-v2.jsonl").write_text(payload);print(json.dumps(m["summary"],sort_keys=True))
if __name__=="__main__":main()
