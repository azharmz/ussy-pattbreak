"""Shadow-replay event-scoped pivot-dependent exit thresholds for multi-pivot T1 executions."""
import argparse,io,json,os
from collections import defaultdict,Counter
from pathlib import Path
import boto3,pandas as pd

def s3():
 return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output",default="audit/exit-reference-shadow.json"); a=ap.parse_args()
 rows=[json.loads(x) for x in (Path(a.input_dir)/"t1-execution.jsonl").read_text().splitlines() if x.strip()]
 ex=[x for x in rows if x["entry_state"]=="EXECUTED_T1_OPEN"]; by=defaultdict(list)
 for x in ex: by[str(x["security_id"])].append(x)
 multi={sid:xs for sid,xs in by.items() if len({float(x["pivot_level"]) for x in xs})>1}
 ptr=json.loads(s3().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key="production/ready/current.json")["Body"].read())
 key=ptr.get("parquet_key") or ptr.get("ready",{}).get("parquet_key")
 if not key: raise ValueError("READY pointer lacks parquet_key")
 df=pd.read_parquet(io.BytesIO(s3().get_object(Bucket=os.environ["R2_BUCKET_NAME"],Key=key)["Body"].read()),columns=["date","security_id","high","close"])
 df["date"]=pd.to_datetime(df["date"]).dt.tz_localize(None); df["security_id"]=df["security_id"].astype(str)
 out=[]; conflicts=Counter()
 for sid,xs in sorted(multi.items()):
  pivots=sorted({float(x["pivot_level"]) for x in xs}); entry=pd.Timestamp(xs[0]["fill_date"]); g=df[(df.security_id==sid)&(df.date>=entry)].sort_values("date")
  first_profit={p:None for p in pivots}; first_rapid={p:None for p in pivots}
  daily_conflict=[]; rapid_conflict=[]
  for _,r in g.iterrows():
   d=r.date.date().isoformat()
   prof={p:(float(r.close)>=p*1.20) for p in pivots if pd.notna(r.close)}
   if prof and len(set(prof.values()))>1: daily_conflict.append(d)
   for p,v in prof.items():
    if v and first_profit[p] is None:first_profit[p]=d
   week=((r.date.normalize()-(entry.normalize()-pd.Timedelta(days=entry.weekday()))).days//7)+1
   rap={p:(week<=3 and float(r.high)>p*1.20) for p in pivots if pd.notna(r.high)}
   if rap and len(set(rap.values()))>1: rapid_conflict.append(d)
   for p,v in rap.items():
    if v and first_rapid[p] is None:first_rapid[p]=d
  if daily_conflict: conflicts["profit_zone_security_conflict"]+=1
  if rapid_conflict: conflicts["rapid_winner_security_conflict"]+=1
  out.append({"security_id":sid,"pivots":pivots,"entry_date":xs[0]["fill_date"],"fill_price":xs[0]["fill_price"],
   "first_profit_zone_date":{str(p):first_profit[p] for p in pivots},"first_rapid_winner_date":{str(p):first_rapid[p] for p in pivots},
   "profit_zone_conflict_dates":daily_conflict,"rapid_winner_conflict_dates":rapid_conflict})
 summary={"multi_pivot_securities":len(out),"ready_as_of":str(df.date.max().date()),**conflicts,
  "profit_zone_conflict_date_count":sum(len(x["profit_zone_conflict_dates"]) for x in out),
  "rapid_winner_conflict_date_count":sum(len(x["rapid_winner_conflict_dates"]) for x in out)}
 p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({"schema":"exit-reference-shadow-v1","summary":summary,"securities":out},indent=2,sort_keys=True)+chr(10));print(json.dumps(summary,sort_keys=True))
if __name__=="__main__":main()
