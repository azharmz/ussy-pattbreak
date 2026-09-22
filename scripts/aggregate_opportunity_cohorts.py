"""Read-only opportunity cohort registry and sufficiency guardrail.

Aggregates PIT linkage outputs across days. It never chooses an eligibility
threshold. A cohort is mature only when its observation horizon has elapsed.
"""
from __future__ import annotations
import argparse,json
from datetime import date
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())

def aggregate(inputs, horizon_days, observation_asof):
    obs=date.fromisoformat(observation_asof)
    cohorts={}
    for p in inputs:
        x=load(p)
        for day,c in x.get("cohorts",{}).items():
            if day in cohorts and cohorts[day]!=c:
                raise ValueError("conflicting cohort "+day)
            cohorts[day]=c
    mature={d:c for d,c in cohorts.items() if (obs-date.fromisoformat(d)).days>=horizon_days}
    bands={}
    keys=sorted({b for c in mature.values() for b in c.get("bands",{})},key=float)
    for b in keys:
        eligible=sum(c["bands"].get(b,{}).get("eligible",0) for c in mature.values())
        hits=sum(c["bands"].get(b,{}).get("later_breakout",0) for c in mature.values())
        bands[b]={"eligible":eligible,"later_breakout":hits,
                  "later_breakout_rate":round(hits/eligible,6) if eligible else None}
    return {
      "semantics":{"status":"research_only","unit":"base_id_as_of_date",
                   "maturity":f"calendar_days>={horizon_days}","thresholds":"descriptive_only"},
      "observation_asof":observation_asof,"horizon_days":horizon_days,
      "cohort_count":len(cohorts),"mature_cohort_count":len(mature),
      "cohort_dates":sorted(cohorts),"mature_cohort_dates":sorted(mature),
      "pooled_mature_bands":bands,
      "decision":{"opportunity_rule_defined":False,
        "sufficient_for_threshold_selection":False,
        "reason":"Registry is an accumulating PIT evidence asset; threshold selection requires a separately approved robustness/sufficiency contract."}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",action="append",required=True)
    ap.add_argument("--horizon-days",type=int,default=5)
    ap.add_argument("--observation-asof",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    x=aggregate(a.input,a.horizon_days,a.observation_asof)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print(json.dumps(x,sort_keys=True))
if __name__=="__main__": main()
