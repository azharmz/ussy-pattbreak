"""Build a compact dashboard opportunity snapshot from frozen morphology + exact READY.

Serving-only projection. It does not create or alter Core methodology states.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import pandas as pd

VERSION="dashboard-opportunity-snapshot-v1"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",default="upstream")
    ap.add_argument("--ready-parquet",required=True)
    ap.add_argument("--output",default="checkpoints/dashboard-opportunities.jsonl")
    ap.add_argument("--price-output",default="checkpoints/dashboard-prices.jsonl")
    a=ap.parse_args()
    inp=Path(a.input_dir)
    raw=json.loads((inp/"raw-oneil-morphology.json").read_text())
    raw_path=inp/"raw-oneil-morphology.jsonl"
    h=hashlib.sha256()
    with raw_path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""): h.update(chunk)
    if h.hexdigest()!=raw["morphology"]["jsonl_sha256"]: raise ValueError("RAW morphology checksum mismatch")
    asof=raw["upstream_frozen_ready"]["as_of_date"]
    ready_path=Path(a.ready_parquet)
    ready_sha=hashlib.sha256(ready_path.read_bytes()).hexdigest()
    frozen_ready=raw["upstream_frozen_ready"]
    expected_ready=str(frozen_ready["source_hash"]).replace("sha256:","")
    if ready_sha!=expected_ready: raise ValueError("READY parquet checksum mismatch")
    df=pd.read_parquet(a.ready_parquet,columns=["date","security_id","ticker","close"])
    df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    d=pd.Timestamp(asof)
    cur=df[df["date"]<=d].sort_values(["security_id","date"]).groupby("security_id",sort=False).tail(1)
    bars={str(x.security_id):(str(x.ticker),float(x.close),x.date.date().isoformat()) for x in cur.itertuples()}
    rows=[]
    with raw_path.open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line)
            if x.get("normalized_status")!="RECOGNIZED" or x.get("asof_date")!=asof or x.get("pivot_level") is None: continue
            sid=str(x["security_id"]); b=bars.get(sid)
            if not b or b[2]!=asof: continue
            pivot=float(x["pivot_level"]); close=b[1]
            rows.append({
                "assessment_id":x["assessment_id"],"base_id":x.get("base_id"),"lineage_id":x.get("lineage_id"),
                "security_id":sid,"ticker":x.get("ticker") or b[0],"pattern_type":x["pattern"],
                "morphology_status":"RECOGNIZED","pivot_level":pivot,"as_of_date":asof,"as_of_close":close,
                "distance_to_pivot_pct":(close/pivot-1)*100 if pivot>0 else None,
                "structural_start":x.get("structural_start"),"structural_end":x.get("structural_end"),
                "pivot_source_date":x.get("pivot_source_date")
            })
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    body="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows)
    out.write_text(body)
    digest=hashlib.sha256(body.encode()).hexdigest()
    meta={"schema_version":VERSION,"as_of_date":asof,"record_count":len(rows),"source_hash":"sha256:"+digest,
          "upstream":{"raw_morphology_sha256":raw["morphology"]["jsonl_sha256"],"ready_source_hash":raw["upstream_frozen_ready"]["source_hash"]}}
    out.with_suffix(".json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    price_rows=[{"security_id":sid,"ticker":ticker,"as_of_date":date,"close":close} for sid,(ticker,close,date) in sorted(bars.items()) if date==asof]
    pout=Path(a.price_output); pout.parent.mkdir(parents=True,exist_ok=True)
    pbody="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in price_rows)
    pout.write_text(pbody)
    pdigest=hashlib.sha256(pbody.encode()).hexdigest()
    pmeta={"schema_version":"dashboard-price-enrichment-v1","as_of_date":asof,"record_count":len(price_rows),"source_hash":"sha256:"+pdigest,"ready_source_hash":"sha256:"+ready_sha}
    pout.with_suffix(".json").write_text(json.dumps(pmeta,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"as_of_date":asof,"record_count":len(rows),"source_hash":"sha256:"+digest,"price_records":len(price_rows),"price_source_hash":"sha256:"+pdigest},sort_keys=True))

if __name__=="__main__": main()
