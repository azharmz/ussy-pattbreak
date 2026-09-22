"""Build Breakout Contract v2 shadow events from exact frozen morphology + READY.

Diagnostic/shadow only. Never publishes production current pointers.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os
from collections import defaultdict
from pathlib import Path
import boto3
import pandas as pd

VOL=1.40
VERSION="pattern-breakout-shadow-v2"

def s3():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def event_id(sid, day, pivot):
    raw=json.dumps([sid,day,format(float(pivot),".12g")],separators=(",",":"))
    return "event_"+hashlib.sha256(raw.encode()).hexdigest()[:32]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output-dir",default="shadow"); a=ap.parse_args()
    inp=Path(a.input_dir); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    frozen=json.loads((inp/"frozen-ready.json").read_text()); meta=json.loads((inp/"raw-oneil-morphology.json").read_text()); mp=inp/"raw-oneil-morphology.jsonl"
    if hashlib.sha256(mp.read_bytes()).hexdigest()!=meta["morphology"]["jsonl_sha256"]: raise ValueError("morphology checksum mismatch")
    if meta["upstream_frozen_ready"]["source_hash"]!=frozen["source_hash"]: raise ValueError("morphology/READY lineage mismatch")
    body=s3().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=frozen["ready"]["parquet_key"])["Body"].read()
    if hashlib.sha256(body).hexdigest()!=frozen["source_hash"].removeprefix("sha256:"): raise ValueError("READY checksum mismatch")
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","close","volume"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize(); asof=pd.Timestamp(frozen["ready"]["as_of_date"])
    histories={}
    for sid,g in df[df["date"]<=asof].sort_values(["security_id","date"]).groupby("security_id",sort=False):
        q=g.copy(); q["prior_close"]=q["close"].shift(1); q["prior50"]=q["volume"].shift(1).rolling(50,min_periods=50).mean(); histories[str(sid)]=q
    hits=[]; recycled=0
    with mp.open(encoding="utf-8") as f:
      for line in f:
        x=json.loads(line)
        if x.get("normalized_status")!="RECOGNIZED" or x.get("pivot_level") is None: continue
        sid=str(x["security_id"]); g=histories.get(sid)
        if g is None or g.empty or g.iloc[-1]["date"]!=asof: continue
        cur=g.iloc[-1]; pivot=float(x["pivot_level"])
        if pd.isna(cur["prior_close"]) or pd.isna(cur["prior50"]) or cur["prior50"]<=0: continue
        ratio=float(cur["volume"])/float(cur["prior50"])
        if not (float(cur["prior_close"])<=pivot<float(cur["close"]) and ratio>=VOL): continue
        if not x.get("base_id") or not x.get("structural_end"): raise ValueError("v2 requires base_id and structural_end")
        prior=g[(g["date"]>=pd.Timestamp(x["structural_end"]))&(g["date"]<asof)].copy()
        prior=prior[(prior["prior_close"]<=pivot)&(prior["close"]>pivot)&prior["prior50"].notna()&(prior["prior50"]>0)]
        prior=prior[(prior["volume"]/prior["prior50"])>=VOL]
        if len(prior): recycled+=1; continue
        hits.append((x,ratio))
    base_pivots=defaultdict(set)
    for x,_ in hits: base_pivots[(str(x["security_id"]),x["base_id"])].add(float(x["pivot_level"]))
    conflicts=[k for k,v in base_pivots.items() if len(v)>1]
    if conflicts: raise ValueError(f"base_id pivot conflict: {conflicts[:3]}")
    groups=defaultdict(list)
    for x,ratio in hits: groups[(str(x["security_id"]),asof.date().isoformat(),float(x["pivot_level"]))].append((x,ratio))
    pivots_by_security=defaultdict(set)
    for sid,day,pivot in groups: pivots_by_security[(sid,day)].add(pivot)
    events=[]
    for (sid,day,pivot),rs in sorted(groups.items()):
        ratios={round(r,12) for _,r in rs}
        if len(ratios)!=1: raise ValueError("consolidated assessments disagree on breakout volume ratio")
        xs=[x for x,_ in rs]
        events.append({"event_id":event_id(sid,day,pivot),"security_id":sid,"signal_date":day,"pivot_level":pivot,
          "breakout_volume_ratio":rs[0][1],"event_state":"SHADOW_TECHNICAL_BREAKOUT_EVENT",
          "competing_pivot":len(pivots_by_security[(sid,day)])>1,
          "assessment_ids":sorted({x["assessment_id"] for x in xs}),"base_ids":sorted({x["base_id"] for x in xs}),
          "lineage_ids":sorted({x["lineage_id"] for x in xs if x.get("lineage_id")}),
          "pattern_types":sorted({x["pattern"] for x in xs}),"structural_ends":sorted({x["structural_end"] for x in xs}),
          "breakout_version":VERSION,"morphology_schema":"oneil-pattern-output-v2","morphology_engine":"33-core-p8-frozen-v1",
          "source_candidate_contract":"pattern-breakout-confirmation-v1"})
    lines="".join(json.dumps(e,sort_keys=True,separators=(",",":"))+"\n" for e in events)
    (out/"breakout-events-v2.jsonl").write_text(lines)
    summary={"schema":"breakout-shadow-v2-summary","as_of_date":asof.date().isoformat(),"v1_assessment_hits":len(hits)+recycled,
      "first_qualifying_assessments":len(hits),"recycled_assessments":recycled,"event_count":len(events),
      "competing_event_count":sum(e["competing_pivot"] for e in events),
      "competing_security_count":len({e["security_id"] for e in events if e["competing_pivot"]}),
      "events_sha256":hashlib.sha256(lines.encode()).hexdigest()}
    expected={
      "2026-09-17":{"counts":(426,293,133,48),"sha256":"d17c87499eba2df6079f9f19025972bd0bafbb69a0783b934855ca78f7ce1992"},
      "2026-09-18":{"counts":(458,265,193,50),"sha256":"a79721966f2cc0257cf197972b3c3c3d500e90ad06606982c707f364b6a61e1f"},
    }
    exp=expected.get(summary["as_of_date"])
    actual=(summary["v1_assessment_hits"],summary["first_qualifying_assessments"],summary["recycled_assessments"],summary["event_count"])
    if exp and (actual!=exp["counts"] or summary["events_sha256"]!=exp["sha256"]):
        raise ValueError(f"frozen baseline reconciliation failed: {summary}")
    (out/"breakout-events-v2-summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    manifest={"stage":"breakout-events-v2","schema_version":"pattern-breakout-event-v2","contract_version":VERSION,
      "signal_date":summary["as_of_date"],"source_hash":"sha256:"+summary["events_sha256"],
      "upstream_morphology_hash":"sha256:"+meta["morphology"]["jsonl_sha256"],
      "upstream_ready_hash":frozen["source_hash"],"summary":summary}
    (out/"breakout-events-v2.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
