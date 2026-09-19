"""Build BREAKOUT_CANDIDATE checkpoint from a frozen morphology artifact and exact READY object."""
from __future__ import annotations
import argparse, hashlib, json, os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
import boto3
import pandas as pd
from pattern_breakout.breakout_v1 import BreakoutObservation, FrozenOneilAssessment, decide_technical_breakout_candidate, BreakoutState
from pattern_breakout.pipeline_v1 import CheckpointLineage, CheckpointStage

VERSION="pattern-breakout-candidate-checkpoint-v1"

def s3_client():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output-dir",default="checkpoints"); a=ap.parse_args()
    inp=Path(a.input_dir); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    frozen=json.loads((inp/"frozen-ready.json").read_text()); raw=json.loads((inp/"raw-oneil-morphology.json").read_text())
    raw_path=inp/"raw-oneil-morphology.jsonl"
    h=hashlib.sha256()
    with raw_path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""): h.update(chunk)
    if h.hexdigest()!=raw["morphology"]["jsonl_sha256"]: raise ValueError("RAW morphology JSONL checksum mismatch")
    if raw["upstream_frozen_ready"]["source_hash"]!=frozen["source_hash"]: raise ValueError("morphology/READY lineage mismatch")
    body=s3_client().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=frozen["ready"]["parquet_key"])["Body"].read()
    expected=frozen["source_hash"].removeprefix("sha256:")
    if hashlib.sha256(body).hexdigest()!=expected: raise ValueError("exact READY object checksum mismatch")
    import io
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","close","volume"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    asof=date.fromisoformat(frozen["ready"]["as_of_date"]); d=pd.Timestamp(asof)
    obs={}
    for sid,g in df.sort_values(["security_id","date"]).groupby("security_id",sort=False):
        g=g[g["date"]<=d]
        if len(g)<2 or g.iloc[-1]["date"]!=d: continue
        cur=g.iloc[-1]; prior=g.iloc[-2]; pv=g.iloc[:-1].tail(50)["volume"]
        obs[str(sid)]=(float(prior["close"]),float(cur["close"]),float(cur["volume"]),float(pv.mean()) if len(pv)==50 else None)
    counts={}; candidates=[]; recognized=0
    with raw_path.open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line)
            if x.get("normalized_status")!="RECOGNIZED": continue
            recognized+=1; sid=str(x["security_id"]); o=obs.get(sid)
            assessment=FrozenOneilAssessment(assessment_id=x["assessment_id"],security_id=sid,assessment_date=asof,pattern_type=x["pattern"],pattern_accepted=True,pivot_level=x.get("pivot_level"),ambiguous=False,rejected=False)
            observation=BreakoutObservation(bar_date=asof,prior_close=o[0] if o else None,close=o[1] if o else None,volume=o[2] if o else None,prior_50_volume_mean=o[3] if o else None,completed_bar=True)
            r=decide_technical_breakout_candidate(assessment=assessment,observation=observation)
            counts[r.breakout_state.value]=counts.get(r.breakout_state.value,0)+1
            if r.breakout_state==BreakoutState.TECHNICAL_BREAKOUT_CANDIDATE: candidates.append(asdict(r))
    payload_lines=[]
    for x in candidates:
        x["signal_date"]=x["signal_date"].isoformat(); x["breakout_state"]=x["breakout_state"].value
        payload_lines.append(json.dumps(x,sort_keys=True,separators=(",",":")))
    jsonl="\n".join(payload_lines)+("\n" if payload_lines else "")
    digest=hashlib.sha256(jsonl.encode()).hexdigest()
    lineage=CheckpointLineage(stage=CheckpointStage.BREAKOUT_CANDIDATE,source_identity=f"raw-oneil-morphology:{raw['source_hash']}",source_hash=digest,schema_version="pattern-breakout-candidate-v1",contract_version=VERSION,producer_commit=os.getenv("GITHUB_SHA","local"),producer_run=os.getenv("GITHUB_RUN_ID","local"),created_at=datetime.now(timezone.utc))
    meta=asdict(lineage); meta["stage"]=lineage.stage.value; meta["created_at"]=lineage.created_at.isoformat(); meta["upstream"]= {"raw_morphology_sha256":raw["morphology"]["jsonl_sha256"],"ready_source_hash":frozen["source_hash"],"as_of_date":asof.isoformat()}; meta["summary"]={"recognized_assessments":recognized,"state_counts":counts,"candidate_count":len(candidates)}
    (out/"breakout-candidate.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    (out/"breakout-candidate.jsonl").write_text(jsonl)
    print(json.dumps(meta["summary"],sort_keys=True))

if __name__=="__main__": main()
