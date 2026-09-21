"""Diagnostic reconstruction of historical close-to-close pivot crossings for one security.

Reads the frozen morphology artifact plus the exact READY parquet referenced by it.
No production checkpoints or pointers are mutated.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os
from pathlib import Path
import boto3
import pandas as pd

def s3_client():
    return boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="upstream")
    ap.add_argument("--security-id", required=True)
    ap.add_argument("--output", default="audit/pivot-lifecycle.json")
    a=ap.parse_args()
    inp=Path(a.input_dir)
    frozen=json.loads((inp/"frozen-ready.json").read_text())
    raw_meta=json.loads((inp/"raw-oneil-morphology.json").read_text())
    raw_path=inp/"raw-oneil-morphology.jsonl"
    h=hashlib.sha256(raw_path.read_bytes()).hexdigest()
    if h != raw_meta["morphology"]["jsonl_sha256"]:
        raise ValueError("RAW morphology JSONL checksum mismatch")
    body=s3_client().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=frozen["ready"]["parquet_key"])["Body"].read()
    if hashlib.sha256(body).hexdigest() != frozen["source_hash"].removeprefix("sha256:"):
        raise ValueError("exact READY object checksum mismatch")
    df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","open","high","low","close","volume"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    g=df[df["security_id"].astype(str)==a.security_id].sort_values("date").copy()
    if g.empty: raise ValueError(f"security_id not found: {a.security_id}")
    asof=pd.Timestamp(frozen["ready"]["as_of_date"])
    g=g[g["date"]<=asof]
    rec=[]
    with raw_path.open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line)
            if str(x.get("security_id"))==a.security_id and x.get("normalized_status")=="RECOGNIZED" and x.get("pivot_level") is not None:
                rec.append(x)
    pivots=sorted({float(x["pivot_level"]) for x in rec})
    out=[]
    for p in pivots:
        crosses=[]
        prev=None
        for _,r in g.iterrows():
            c=float(r["close"])
            if prev is not None and prev <= p < c:
                crosses.append({"date":r["date"].date().isoformat(),"prior_close":prev,"open":float(r["open"]),"high":float(r["high"]),"low":float(r["low"]),"close":c,"gap_above_pivot":float(r["open"])>p})
            prev=c
        contributors=[x for x in rec if abs(float(x["pivot_level"])-p)<1e-9]
        out.append({"pivot_level":p,"assessment_count":len(contributors),
            "patterns":sorted({x.get("pattern") for x in contributors}),
            "pivot_source_dates":sorted({x.get("pivot_source_date") for x in contributors if x.get("pivot_source_date")}),
            "structural_starts":sorted({x.get("structural_start") for x in contributors if x.get("structural_start")}),
            "structural_ends":sorted({x.get("structural_end") for x in contributors if x.get("structural_end")}),
            "crossings":crosses})
    payload={"security_id":a.security_id,"ready_as_of_date":asof.date().isoformat(),
        "price_first_date":g.iloc[0]["date"].date().isoformat(),"price_last_date":g.iloc[-1]["date"].date().isoformat(),
        "recognized_pivot_count":len(pivots),"pivots":out}
    path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"security_id":a.security_id,"pivots":len(pivots),"crossings":sum(len(x["crossings"]) for x in out)},sort_keys=True))
if __name__=="__main__": main()
