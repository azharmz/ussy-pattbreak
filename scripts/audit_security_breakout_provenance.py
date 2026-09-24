from __future__ import annotations
import argparse,hashlib,io,json,os
from collections import defaultdict
from pathlib import Path
import boto3,pandas as pd
VOL=1.40
def s3():
 return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input-dir",default="upstream");ap.add_argument("--security-id",required=True);ap.add_argument("--output",default="audit/security-breakout-provenance.json");a=ap.parse_args()
 inp=Path(a.input_dir); frozen=json.loads((inp/"frozen-ready.json").read_text()); meta=json.loads((inp/"raw-oneil-morphology.json").read_text()); mp=inp/"raw-oneil-morphology.jsonl"
 if hashlib.sha256(mp.read_bytes()).hexdigest()!=meta["morphology"]["jsonl_sha256"]: raise ValueError("morphology checksum mismatch")
 body=s3().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=frozen["ready"]["parquet_key"])["Body"].read()
 if hashlib.sha256(body).hexdigest()!=frozen["source_hash"].removeprefix("sha256:"): raise ValueError("READY checksum mismatch")
 df=pd.read_parquet(io.BytesIO(body),columns=["date","security_id","ticker","close","volume"]);df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize();asof=pd.Timestamp(frozen["ready"]["as_of_date"])
 g=df[(df["security_id"].astype(str)==a.security_id)&(df["date"]<=asof)].sort_values("date").copy();g["prior_close"]=g["close"].shift(1);g["prior50"]=g["volume"].shift(1).rolling(50,min_periods=50).mean()
 if g.empty or g.iloc[-1]["date"]!=asof: raise ValueError("security missing at READY as-of")
 cur=g.iloc[-1]; ratio=float(cur["volume"])/float(cur["prior50"])
 rec=[]
 for line in mp.open(encoding="utf-8"):
  x=json.loads(line)
  if str(x.get("security_id"))==a.security_id and x.get("normalized_status")=="RECOGNIZED" and x.get("pivot_level") is not None: rec.append(x)
 hits=[]; recycled=[]
 for x in rec:
  p=float(x["pivot_level"])
  if not(float(cur["prior_close"])<=p<float(cur["close"]) and ratio>=VOL): continue
  prior=g[(g["date"]>=pd.Timestamp(x["structural_end"]))&(g["date"]<asof)].copy()
  prior=prior[(prior["prior_close"]<=p)&(prior["close"]>p)&prior["prior50"].notna()&(prior["prior50"]>0)]
  prior=prior[(prior["volume"]/prior["prior50"])>=VOL]
  (recycled if len(prior) else hits).append(x)
 groups=defaultdict(list)
 for x in hits: groups[float(x["pivot_level"])].append(x)
 events=[]
 for p,xs in sorted(groups.items()):
  events.append({"pivot_level":p,"assessment_count":len(xs),"base_count":len({x["base_id"] for x in xs}),"lineage_count":len({x.get("lineage_id") for x in xs}),"patterns":sorted({x["pattern"] for x in xs}),"contributors":[{k:x.get(k) for k in ["assessment_id","base_id","lineage_id","pattern","candidate_semantics","structural_signature","structural_start","structural_end","pivot_source_date","depth_pct","faults"]} for x in xs]})
 out={"security_id":a.security_id,"ticker":str(cur.get("ticker")),"signal_date":asof.date().isoformat(),"prior_close":float(cur["prior_close"]),"close":float(cur["close"]),"volume_ratio":ratio,"first_qualifying_assessments":len(hits),"recycled_assessments":len(recycled),"events":events}
 p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({k:out[k] for k in ["ticker","signal_date","prior_close","close","volume_ratio","first_qualifying_assessments","recycled_assessments"]}|{"event_count":len(events),"base_counts":[e["base_count"] for e in events]},sort_keys=True))
if __name__=="__main__":main()
