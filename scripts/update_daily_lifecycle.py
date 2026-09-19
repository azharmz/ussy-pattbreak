"""Advance OPEN/EXIT_PENDING positions causally against the current canonical READY snapshot."""
from __future__ import annotations
import argparse, hashlib, io, json, os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
import boto3, pandas as pd
from pattern_breakout.ready_runtime_v1 import read_and_freeze_ready
from pattern_breakout.lifecycle_v1 import PatternBreakoutPosition, PositionState, execute_pending_exit
from pattern_breakout.exit_v1 import PositionTechnicalContext, DailyTechnicalObservation, WeeklyTechnicalObservation, evaluate_daily_technical_exit, evaluate_weekly_10w_ma_exit
from pattern_breakout.eight_week_rule_v1 import EightWeekRuleContext, assess_eight_week_rule
from pattern_breakout.exit_arbitration_v1 import arbitrate_exit
from pattern_breakout.lifecycle_arbitration_v1 import apply_exit_arbitration
from pattern_breakout.lifecycle_store_v1 import publish_lifecycle_checkpoint

VERSION="pattern-breakout-daily-lifecycle-checkpoint-v1"

def client():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def pos(x):
    return PatternBreakoutPosition(position_id=x["position_id"],candidate_id=x["candidate_id"],security_id=str(x["security_id"]),entry_date=date.fromisoformat(x["entry_date"]) if x.get("entry_date") else None,entry_price=x.get("entry_price"),pivot_level=x.get("pivot_level"),state=PositionState(x["state"]),exit_signal_date=date.fromisoformat(x["exit_signal_date"]) if x.get("exit_signal_date") else None,exit_reason=x.get("exit_reason"),exit_date=date.fromisoformat(x["exit_date"]) if x.get("exit_date") else None,exit_price=x.get("exit_price"))

def dump(p, first, last):
    y=asdict(p)
    for k in ("entry_date","exit_signal_date","exit_date"): y[k]=y[k].isoformat() if y[k] else None
    y["state"]=y["state"].value; y["eight_week_first_rapid_winner_date"]=first.isoformat() if first else None; y["last_evaluated_date"]=last.isoformat() if last else None
    return y

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output-dir",default="checkpoints"); a=ap.parse_args()
    inp=Path(a.input_dir); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((inp/"open-positions.json").read_text()); raw=(inp/"open-positions.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=meta["source_hash"].removeprefix("sha256:"): raise ValueError("position checkpoint checksum mismatch")
    frozen,body=read_and_freeze_ready(client(),os.environ["R2_BUCKET_NAME"],producer_commit=os.getenv("GITHUB_SHA","local"),producer_run=os.getenv("GITHUB_RUN_ID","local"))
    ready_asof=date.fromisoformat(frozen["ready"]["as_of_date"])
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","open","high","close","volume"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None); df["security_id"]=df["security_id"].astype(str)
    output=[]; counts={}; reasons={}
    for line in raw.decode().splitlines():
        x=json.loads(line); p=pos(x); first=date.fromisoformat(x["eight_week_first_rapid_winner_date"]) if x.get("eight_week_first_rapid_winner_date") else None; last=date.fromisoformat(x["last_evaluated_date"]) if x.get("last_evaluated_date") else None
        g=df[df.security_id==p.security_id].sort_values("date")
        if p.state==PositionState.EXIT_PENDING:
            ng=g[g.date.dt.date>p.exit_signal_date]
            if len(ng): p=execute_pending_exit(p,next_session_date=ng.iloc[0].date.date(),next_open=float(ng.iloc[0].open) if pd.notna(ng.iloc[0].open) else None)
        if p.state==PositionState.OPEN:
            start=max(p.entry_date,last) if last else p.entry_date
            bars=g[(g.date.dt.date>=start)&(g.date.dt.date<=ready_asof)]
            if last: bars=bars[bars.date.dt.date>last]
            for _,r in bars.iterrows():
                d=r.date.date(); ctx=PositionTechnicalContext(p.position_id,p.security_id,p.entry_date,float(p.entry_price),float(p.pivot_level))
                daily=evaluate_daily_technical_exit(position=ctx,observation=DailyTechnicalObservation(d,float(r.close) if pd.notna(r.close) else None,True))
                ewctx=EightWeekRuleContext(p.entry_date,float(p.pivot_level),first)
                ew=assess_eight_week_rule(context=ewctx,observation_date=d,high=float(r.high) if pd.notna(r.high) else None,completed_bar=True); first=ew.first_rapid_winner_date
                ev=[daily]
                # Weekly evidence only on a completed Friday session. Build completed weekly bars from daily READY.
                if r.date.weekday()==4:
                    hist=g[g.date<=r.date].copy(); hist["week"]=hist.date.dt.to_period("W-FRI")
                    w=hist.groupby("week").agg(close=("close","last"),volume=("volume","sum")).reset_index()
                    if len(w)>=10:
                        ma=float(w.tail(10).close.mean()); av=float(w.iloc[:-1].tail(10).volume.mean()) if len(w)>=11 else None
                        if av is not None:
                            ev.append(evaluate_weekly_10w_ma_exit(position=ctx,observation=WeeklyTechnicalObservation(d,float(r.close),ma,float(w.iloc[-1].volume),av,True)))
                arb=arbitrate_exit(ev,ew); p=apply_exit_arbitration(p,arb); last=d
                if p.state!=PositionState.OPEN: break
        y=dump(p,first,last); output.append(y); counts[y["state"]]=counts.get(y["state"],0)+1
        if y.get("exit_reason"): reasons[y["exit_reason"]]=reasons.get(y["exit_reason"],0)+1
    payload="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in output); digest=hashlib.sha256(payload.encode()).hexdigest()
    m={"stage":"lifecycle","schema_version":"pattern-breakout-position-v1.1","contract_version":VERSION,"source_identity":f"positions:{meta['source_hash']}","source_hash":f"sha256:{digest}","created_at":datetime.now(timezone.utc).isoformat(),"producer_commit":os.getenv("GITHUB_SHA","local"),"producer_run":os.getenv("GITHUB_RUN_ID","local"),"upstream_position_hash":meta["source_hash"],"execution_ready":{"source_identity":frozen["source_identity"],"source_hash":frozen["source_hash"],"as_of_date":frozen["ready"]["as_of_date"],"parquet_key":frozen["ready"]["parquet_key"]},"summary":{"position_count":len(output),"state_counts":counts,"exit_reasons":reasons}}
    (out/"lifecycle.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n"); (out/"lifecycle.jsonl").write_text(payload); print(json.dumps(m["summary"],sort_keys=True))
if __name__=="__main__": main()
