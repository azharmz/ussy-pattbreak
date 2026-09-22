"""Read-only historical linkage research for setup proximity vs later breakout.

Uses daily base-level evidence snapshots plus later canonical breakout-event rows.
It measures outcomes for descriptive distance bands and never selects a threshold.
"""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from datetime import date
from pathlib import Path

BANDS=(1,2,3,5,10,20)

def load_jsonl(p):
 return [json.loads(x) for x in Path(p).read_text().splitlines() if x]

def research(snapshots, events):
 ev=defaultdict(list)
 for e in events:
  for bid in e.get("base_ids") or []:
   ev[str(bid)].append(e)
 out={"semantics":{"unit":"base_id_as_of_date","outcome":"later_first_qualifying_breakout_event","thresholds":"descriptive_only"},"cohorts":{}}
 for p in snapshots:
  rows=load_jsonl(p); asof=rows[0]["as_of_date"] if rows else None
  bases={}
  for r in rows: bases[str(r["base_id"])]=r
  cohort={"base_ids":len(bases),"below_pivot":0,"bands":{}}
  for b in BANDS: cohort["bands"][str(b)]={"eligible":0,"later_breakout":0,"days_to_breakout":[]}
  for bid,r in bases.items():
   pivot=float(r["pivot_level"]); close=float(r["as_of_close"])
   if close>=pivot: continue
   cohort["below_pivot"]+=1; gap=(pivot/close-1)*100
   later=[]
   for e in ev.get(bid,[]):
    d=(date.fromisoformat(e["signal_date"])-date.fromisoformat(asof)).days
    if d>0: later.append(d)
   for b in BANDS:
    if gap<=b:
     z=cohort["bands"][str(b)]; z["eligible"]+=1
     if later: z["later_breakout"]+=1; z["days_to_breakout"].append(min(later))
  for z in cohort["bands"].values():
   ds=sorted(z.pop("days_to_breakout")); n=z["eligible"]
   z["later_breakout_rate"]=round(z["later_breakout"]/n,6) if n else None
   z["median_days_to_breakout"]=ds[len(ds)//2] if ds else None
  out["cohorts"][asof]=cohort
 out["decision"]={"opportunity_rule_defined":False,"reason":"Historical linkage is descriptive; no distance/lifecycle threshold is selected."}
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--snapshot",action="append",required=True); ap.add_argument("--events",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
 x=research(a.snapshot,load_jsonl(a.events)); Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n"); print(json.dumps(x,sort_keys=True))
if __name__=="__main__": main()
