"""Diagnostic audit: first qualifying breakout vs recycled pivot for one frozen morphology run.

For each current TECHNICAL_BREAKOUT_CANDIDATE, searches only prior completed bars
on/after that assessment's structural_end. A prior event qualifies when the same
production crossing rule holds and volume >= 1.40x prior 50-bar mean.
Diagnostic only; does not mutate production checkpoints.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os
from collections import Counter, defaultdict
from pathlib import Path
import boto3
import pandas as pd

VOL_THRESHOLD=1.40

def s3_client():
    return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],
      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output",default="audit/first-breakout-audit.json"); a=ap.parse_args()
    inp=Path(a.input_dir); frozen=json.loads((inp/"frozen-ready.json").read_text()); meta=json.loads((inp/"raw-oneil-morphology.json").read_text()); rawp=inp/"raw-oneil-morphology.jsonl"
    if hashlib.sha256(rawp.read_bytes()).hexdigest()!=meta["morphology"]["jsonl_sha256"]: raise ValueError("morphology checksum mismatch")
    body=s3_client().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=frozen["ready"]["parquet_key"])["Body"].read()
    if hashlib.sha256(body).hexdigest()!=frozen["source_hash"].removeprefix("sha256:"): raise ValueError("READY checksum mismatch")
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","close","volume"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize(); asof=pd.Timestamp(frozen["ready"]["as_of_date"])
    histories={}
    for sid,g in df[df["date"]<=asof].sort_values(["security_id","date"]).groupby("security_id",sort=False):
        q=g.copy(); q["prior_close"]=q["close"].shift(1); q["prior50_vol_mean"]=q["volume"].shift(1).rolling(50,min_periods=50).mean(); histories[str(sid)]=q
    rows=[]
    with rawp.open(encoding="utf-8") as f:
      for line in f:
        x=json.loads(line)
        if x.get("normalized_status")!="RECOGNIZED" or x.get("pivot_level") is None: continue
        sid=str(x["security_id"]); g=histories.get(sid)
        if g is None or g.empty or g.iloc[-1]["date"]!=asof: continue
        cur=g.iloc[-1]; p=float(x["pivot_level"])
        if pd.isna(cur["prior_close"]) or not (float(cur["prior_close"])<=p<float(cur["close"])): continue
        if pd.isna(cur["prior50_vol_mean"]) or float(cur["prior50_vol_mean"])<=0: continue
        vr=float(cur["volume"])/float(cur["prior50_vol_mean"])
        if vr < VOL_THRESHOLD: continue
        start=x.get("structural_end") or x.get("pivot_source_date") or x.get("structural_start")
        if not start: raise ValueError(f"assessment lacks eligibility anchor: {x['assessment_id']}")
        start_ts=pd.Timestamp(start)
        prior=g[(g["date"]>=start_ts)&(g["date"]<asof)].copy()
        prior=prior[(prior["prior_close"]<=p)&(prior["close"]>p)&prior["prior50_vol_mean"].notna()&(prior["prior50_vol_mean"]>0)]
        prior["volume_ratio"]=prior["volume"]/prior["prior50_vol_mean"]
        qual=prior[prior["volume_ratio"]>=VOL_THRESHOLD]
        rows.append({"assessment_id":x["assessment_id"],"security_id":sid,"pattern":x.get("pattern"),"base_id":x.get("base_id"),"lineage_id":x.get("lineage_id"),"pivot_level":p,"structural_end":x.get("structural_end"),"current_volume_ratio":vr,
          "classification":"RECYCLED_PIVOT" if len(qual) else "FIRST_QUALIFYING_BREAKOUT",
          "prior_qualifying_count":int(len(qual)),
          "first_prior_qualifying_date":qual.iloc[0]["date"].date().isoformat() if len(qual) else None,
          "last_prior_qualifying_date":qual.iloc[-1]["date"].date().isoformat() if len(qual) else None})
    cls=Counter(r["classification"] for r in rows)
    bysec=defaultdict(list)
    for r in rows: bysec[r["security_id"]].append(r)
    sec_summary=[]
    for sid,rs in bysec.items():
        sec_summary.append({"security_id":sid,"assessment_candidates":len(rs),
          "first_assessments":sum(r["classification"]=="FIRST_QUALIFYING_BREAKOUT" for r in rs),
          "recycled_assessments":sum(r["classification"]=="RECYCLED_PIVOT" for r in rs),
          "unique_pivots":len({r["pivot_level"] for r in rs}),
          "first_unique_pivots":len({r["pivot_level"] for r in rs if r["classification"]=="FIRST_QUALIFYING_BREAKOUT"}),
          "recycled_unique_pivots":len({r["pivot_level"] for r in rs if r["classification"]=="RECYCLED_PIVOT"})})
    survivors=[r for r in rows if r["classification"]=="FIRST_QUALIFYING_BREAKOUT"]\n    def groups(keyfn):\n        d=defaultdict(list)\n        for r in survivors: d[keyfn(r)].append(r)\n        return d\n    by_base=groups(lambda r:(r["security_id"],r.get("base_id")))\n    by_lineage=groups(lambda r:(r["security_id"],r.get("lineage_id")))\n    by_pivot=groups(lambda r:(r["security_id"],r["pivot_level"]))\n    by_base_pivot=groups(lambda r:(r["security_id"],r.get("base_id"),r["pivot_level"]))\n    identity_summary={\n      "surviving_assessments":len(survivors),\n      "unique_security_pivots":len(by_pivot),\n      "unique_security_base_ids":len(by_base),\n      "unique_security_lineage_ids":len(by_lineage),\n      "unique_security_base_pivots":len(by_base_pivot),\n      "base_groups_with_multiple_assessments":sum(len(v)>1 for v in by_base.values()),\n      "lineage_groups_with_multiple_assessments":sum(len(v)>1 for v in by_lineage.values()),\n      "pivot_groups_with_multiple_assessments":sum(len(v)>1 for v in by_pivot.values()),\n      "base_groups_spanning_multiple_pivots":sum(len({r["pivot_level"] for r in v})>1 for v in by_base.values()),\n      "lineage_groups_spanning_multiple_pivots":sum(len({r["pivot_level"] for r in v})>1 for v in by_lineage.values()),\n      "pivot_groups_spanning_multiple_base_ids":sum(len({r.get("base_id") for r in v})>1 for v in by_pivot.values()),\n      "pivot_groups_spanning_multiple_lineage_ids":sum(len({r.get("lineage_id") for r in v})>1 for v in by_pivot.values()),\n    }\n    payload={"schema":"first-breakout-audit-v2","as_of_date":asof.date().isoformat(),"volume_threshold":VOL_THRESHOLD,
      "eligibility_anchor":"assessment.structural_end (fallback pivot_source_date/structural_start)",
      "candidate_assessments":len(rows),"classification_counts":dict(cls),
      "unique_securities":len(bysec),"unique_security_pivots":len({(r["security_id"],r["pivot_level"]) for r in rows}),
      "security_summary":sorted(sec_summary,key=lambda z:(-z["assessment_candidates"],z["security_id"])),"survivor_identity_summary":identity_summary,"rows":rows}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({**{k:payload[k] for k in ["as_of_date","candidate_assessments","classification_counts","unique_securities","unique_security_pivots"]},"survivor_identity_summary":identity_summary},sort_keys=True))
if __name__=="__main__": main()
