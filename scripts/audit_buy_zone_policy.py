"""Audit competing v2 pivot events without selecting a winner.

Extends shadow output with morphology-supported structural features so competing
pivots can be studied without introducing an unsupported ranking policy.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os
from collections import defaultdict
from pathlib import Path
import boto3
import pandas as pd

VOL=1.40

def s3():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output",default="audit/competing-pivots.json"); a=ap.parse_args()
    inp=Path(a.input_dir); frozen=json.loads((inp/"frozen-ready.json").read_text()); meta=json.loads((inp/"raw-oneil-morphology.json").read_text()); mp=inp/"raw-oneil-morphology.jsonl"
    if hashlib.sha256(mp.read_bytes()).hexdigest()!=meta["morphology"]["jsonl_sha256"]: raise ValueError("morphology checksum mismatch")
    body=s3().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=frozen["ready"]["parquet_key"])["Body"].read()
    if hashlib.sha256(body).hexdigest()!=frozen["source_hash"].removeprefix("sha256:"): raise ValueError("READY checksum mismatch")
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","close","volume"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize(); asof=pd.Timestamp(frozen["ready"]["as_of_date"])
    histories={}
    for sid,g in df[df["date"]<=asof].sort_values(["security_id","date"]).groupby("security_id",sort=False):
        q=g.copy(); q["prior_close"]=q["close"].shift(1); q["prior50"]=q["volume"].shift(1).rolling(50,min_periods=50).mean(); histories[str(sid)]=q
    survivors=[]
    with mp.open(encoding="utf-8") as f:
      for line in f:
        x=json.loads(line)
        if x.get("normalized_status")!="RECOGNIZED" or x.get("pivot_level") is None: continue
        sid=str(x["security_id"]); g=histories.get(sid)
        if g is None or g.empty or g.iloc[-1]["date"]!=asof: continue
        cur=g.iloc[-1]; p=float(x["pivot_level"])
        if pd.isna(cur["prior_close"]) or pd.isna(cur["prior50"]) or cur["prior50"]<=0: continue
        ratio=float(cur["volume"])/float(cur["prior50"])
        if not (float(cur["prior_close"])<=p<float(cur["close"]) and ratio>=VOL): continue
        if not x.get("base_id") or not x.get("structural_end"): raise ValueError("missing v2 structural identity")
        prior=g[(g["date"]>=pd.Timestamp(x["structural_end"]))&(g["date"]<asof)].copy()
        prior=prior[(prior["prior_close"]<=p)&(prior["close"]>p)&prior["prior50"].notna()&(prior["prior50"]>0)]
        if len(prior[(prior["volume"]/prior["prior50"])>=VOL]): continue
        survivors.append(x)
    groups=defaultdict(list)
    for x in survivors: groups[(str(x["security_id"]),float(x["pivot_level"]))].append(x)
    bysec=defaultdict(list)
    for (sid,p),xs in groups.items():
        bysec[sid].append((p,xs))
    competing=[]
    for sid,events in sorted(bysec.items()):
        if len(events)<=1: continue
        cur=histories[sid].iloc[-1]; close=float(cur["close"])
        rec={"security_id":sid,"signal_date":asof.date().isoformat(),"close":close,"event_count":len(events),"events":[],"within_5pct_event_count":0}
        for p,xs in sorted(events):
            starts=sorted({x.get("structural_start") for x in xs if x.get("structural_start")})
            ends=sorted({x.get("structural_end") for x in xs if x.get("structural_end")})
            sources=sorted({x.get("pivot_source_date") for x in xs if x.get("pivot_source_date")})
            semantics=sorted({x.get("candidate_semantics") for x in xs if x.get("candidate_semantics")})
            dist=(close/p-1)*100
            rec["events"].append({"pivot_level":p,"distance_above_pivot_pct":dist,"within_5pct_at_signal":dist<=5.0,
              "assessment_count":len(xs),"base_count":len({x["base_id"] for x in xs}),
              "lineage_count":len({x.get("lineage_id") for x in xs if x.get("lineage_id")}),
              "patterns":sorted({x.get("pattern") for x in xs}),"candidate_semantics":semantics,
              "structural_starts":starts,"structural_ends":ends,"pivot_source_dates":sources,
              "depth_pct_min":min(float(x["depth_pct"]) for x in xs if x.get("depth_pct") is not None) if any(x.get("depth_pct") is not None for x in xs) else None,
              "depth_pct_max":max(float(x["depth_pct"]) for x in xs if x.get("depth_pct") is not None) if any(x.get("depth_pct") is not None for x in xs) else None})
        rec["within_5pct_event_count"]=sum(e["within_5pct_at_signal"] for e in rec["events"])
        competing.append(rec)
    summary={"as_of_date":asof.date().isoformat(),"surviving_assessments":len(survivors),"event_count":len(groups),
      "competing_security_count":len(competing),"competing_event_count":sum(x["event_count"] for x in competing),
      "pivot_count_distribution":dict(sorted(__import__("collections").Counter(x["event_count"] for x in competing).items())),
      "securities_with_open_right_edge":sum(any("OPEN_RIGHT_EDGE" in s for e in x["events"] for s in e["candidate_semantics"]) for x in competing),
      "securities_with_multiple_open_right_edge_events":sum(sum(any("OPEN_RIGHT_EDGE" in s for s in e["candidate_semantics"]) for e in x["events"])>1 for x in competing),
      "within_5pct_event_count":sum(sum(e["within_5pct_at_signal"] for e in x["events"]) for x in competing),
      "securities_with_exactly_one_within_5pct":sum(x["within_5pct_event_count"]==1 for x in competing),
      "securities_with_multiple_within_5pct":sum(x["within_5pct_event_count"]>1 for x in competing),
      "securities_with_zero_within_5pct":sum(x["within_5pct_event_count"]==0 for x in competing)}
    payload={"schema":"competing-pivot-audit-v1","summary":summary,"securities":competing}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2,sort_keys=True)+chr(10))
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
