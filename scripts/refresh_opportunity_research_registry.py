"""Refresh pooled Opportunity research evidence from durable PIT cohorts.

Read-only with respect to production. Reads research cohort snapshots and canonical
breakout-event indexes from R2, then writes only under the research namespace.
No eligibility threshold or dashboard projection is created.
"""
from __future__ import annotations
import argparse,json,os,tempfile
from datetime import date
from pathlib import Path
import boto3
from research_opportunity_breakout_linkage import research

PREFIX="pattern-breakout/research/opportunity-cohorts"
EVENT_PREFIX="pattern-breakout/production/breakout-events-v2/by-signal-date"

def s3():
 return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def list_keys(c,b,prefix):
 out=[]; token=None
 while True:
  kw={"Bucket":b,"Prefix":prefix}
  if token: kw["ContinuationToken"]=token
  r=c.list_objects_v2(**kw); out += [x["Key"] for x in r.get("Contents",[])]
  if not r.get("IsTruncated"): return out
  token=r["NextContinuationToken"]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--observation-asof",required=True); ap.add_argument("--horizon-days",type=int,default=5); a=ap.parse_args()
 c=s3(); b=os.environ["R2_BUCKET_NAME"]; obs=date.fromisoformat(a.observation_asof)
 indexes=[k for k in list_keys(c,b,PREFIX+"/by-as-of/") if k.endswith("/index.json")]
 manifests=[]
 for k in indexes:
  m=json.loads(c.get_object(Bucket=b,Key=k)["Body"].read())
  if date.fromisoformat(m["as_of_date"])<=obs: manifests.append(m)
 events=[]
 for k in list_keys(c,b,EVENT_PREFIX+"/"):
  if not k.endswith(".json"): continue
  day=k.rsplit("/",1)[-1][:-5]
  try: d=date.fromisoformat(day)
  except ValueError: continue
  if d>obs: continue
  idx=json.loads(c.get_object(Bucket=b,Key=k)["Body"].read())
  raw=c.get_object(Bucket=b,Key=idx["jsonl_key"])["Body"].read().decode()
  events += [json.loads(x) for x in raw.splitlines() if x]
 with tempfile.TemporaryDirectory() as td:
  ps=[]
  for i,m in enumerate(sorted(manifests,key=lambda x:x["as_of_date"])):
   p=Path(td)/f"{i}.jsonl"; p.write_bytes(c.get_object(Bucket=b,Key=m["jsonl_key"])["Body"].read()); ps.append(str(p))
  result=research(ps,events) if ps else {"cohorts":{}}
 mature={d:x for d,x in result.get("cohorts",{}).items() if (obs-date.fromisoformat(d)).days>=a.horizon_days}
 pooled={}
 for band in ("1","2","3","5","10","20"):
  eligible=sum(x["bands"][band]["eligible"] for x in mature.values())
  hits=sum(x["bands"][band]["later_breakout"] for x in mature.values())
  pooled[band]={"eligible":eligible,"later_breakout":hits,"later_breakout_rate":round(hits/eligible,6) if eligible else None}
 out={"schema":"opportunity-research-registry-v1","status":"RESEARCH_ONLY","observation_asof":a.observation_asof,
      "horizon_days":a.horizon_days,"cohort_count":len(result.get("cohorts",{})),"mature_cohort_count":len(mature),
      "cohort_dates":sorted(result.get("cohorts",{})),"mature_cohort_dates":sorted(mature),
      "pooled_mature_bands":pooled,"eligibility_rule_defined":False,"sufficient_for_threshold_selection":False,
      "note":"Pooled descriptive PIT evidence only; no Opportunity threshold or lifecycle rule selected."}
 body=(json.dumps(out,indent=2,sort_keys=True)+"\n").encode()
 key=f"{PREFIX}/registry/{a.observation_asof}.json"
 c.put_object(Bucket=b,Key=key,Body=body,ContentType="application/json")
 c.put_object(Bucket=b,Key=f"{PREFIX}/registry/current.json",Body=body,ContentType="application/json")
 print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
