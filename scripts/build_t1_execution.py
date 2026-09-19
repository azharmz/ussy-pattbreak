"""Build causal T1_EXECUTION checkpoint from frozen breakout candidates and a later READY snapshot."""
from __future__ import annotations
import argparse, hashlib, io, json, os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
import boto3, pandas as pd
from pattern_breakout.entry_v1 import decide_pattern_breakout_t1_open
from pattern_breakout.ready_runtime_v1 import read_and_freeze_ready

VERSION="pattern-breakout-t1-checkpoint-v1"

def client():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output-dir",default="checkpoints"); a=ap.parse_args()
    inp=Path(a.input_dir); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((inp/"breakout-candidate.json").read_text()); cp=inp/"breakout-candidate.jsonl"
    raw=cp.read_bytes(); expected=meta["source_hash"].removeprefix("sha256:")
    if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError("candidate checkpoint checksum mismatch")
    signal_date=date.fromisoformat(meta["upstream"]["as_of_date"])
    s3=client(); frozen, body=read_and_freeze_ready(s3,os.environ["R2_BUCKET_NAME"],producer_commit=os.getenv("GITHUB_SHA","local"),producer_run=os.getenv("GITHUB_RUN_ID","local"))
    execution_asof=date.fromisoformat(frozen["ready"]["as_of_date"])
    if execution_asof<=signal_date: raise ValueError(f"READY {execution_asof} does not contain a post-signal session after {signal_date}")
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","open"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.date
    nextbars={}
    for sid,g in df[df["date"]>signal_date].sort_values(["security_id","date"]).groupby("security_id",sort=False):
        r=g.iloc[0]; nextbars[str(sid)]=(r["date"],float(r["open"]) if pd.notna(r["open"]) else None)
    rows=[]; counts={}
    for line in raw.decode().splitlines():
        x=json.loads(line); nb=nextbars.get(str(x["security_id"]))
        r=decide_pattern_breakout_t1_open(candidate_id=x["candidate_id"],security_id=str(x["security_id"]),signal_date=date.fromisoformat(x["signal_date"]),candidate_stage=x["candidate_stage"],pivot_level=x["pivot_level"],next_session_date=nb[0] if nb else None,next_open=nb[1] if nb else None)
        y=asdict(r); y["signal_date"]=y["signal_date"].isoformat(); y["next_session_date"]=y["next_session_date"].isoformat() if y["next_session_date"] else None; y["fill_date"]=y["fill_date"].isoformat() if y["fill_date"] else None; y["entry_state"]=y["entry_state"].value
        rows.append(y); counts[y["entry_state"]]=counts.get(y["entry_state"],0)+1
    payload="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows); digest=hashlib.sha256(payload.encode()).hexdigest()
    summary={"signal_date":signal_date.isoformat(),"execution_ready_as_of":execution_asof.isoformat(),"candidate_count":len(rows),"state_counts":counts}
    m={"stage":"t1_execution","schema_version":"pattern-breakout-t1-v1","contract_version":VERSION,"source_identity":f"breakout-candidate:{meta['source_hash']}","source_hash":f"sha256:{digest}","created_at":datetime.now(timezone.utc).isoformat(),"producer_commit":os.getenv("GITHUB_SHA","local"),"producer_run":os.getenv("GITHUB_RUN_ID","local"),"upstream_candidate_hash":meta["source_hash"],"execution_ready":{"source_identity":frozen["source_identity"],"source_hash":frozen["source_hash"],"as_of_date":frozen["ready"]["as_of_date"],"parquet_key":frozen["ready"]["parquet_key"]},"summary":summary}
    (out/"t1-execution.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n"); (out/"t1-execution.jsonl").write_text(payload)
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
