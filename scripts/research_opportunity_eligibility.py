"""Read-only research on pre-breakout setup eligibility.

This deliberately measures distributions; it does not define an Opportunity
threshold, liveness state, expiry rule, or supersession rule.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

def _q(vals):
    if not vals: return {}
    a=sorted(vals); n=len(a)
    def at(p): return a[round((n-1)*p)]
    return {k:round(at(p),4) for k,p in (("p0",0),("p10",.1),("p25",.25),("p50",.5),("p75",.75),("p90",.9),("p100",1))}

def research(rows):
    bases=defaultdict(list)
    for r in rows: bases[str(r["base_id"])].append(r)
    reps=[]
    for bid,g in bases.items():
        g=sorted(g,key=lambda r:(str(r.get("as_of_date","")),str(r.get("assessment_id",""))))
        r=g[-1]
        pivot=float(r["pivot_level"]); close=float(r["as_of_close"])
        reps.append({**r,"distance_pct":(close/pivot-1)*100})
    per_security=Counter(str(r["security_id"]) for r in reps)
    per_lineage=Counter(str(r["lineage_id"]) for r in reps)
    distances=[r["distance_pct"] for r in reps]
    below=[-r["distance_pct"] for r in reps if r["distance_pct"]<0]
    above=[r["distance_pct"] for r in reps if r["distance_pct"]>=0]
    bands=[0,1,2,3,5,10,20]
    return {
      "semantics":{"unit":"base_id","status":"research_only_not_opportunity","thresholds":"descriptive_only"},
      "cardinality":{"base_ids":len(reps),"securities":len(per_security),"lineages":len(per_lineage),
        "bases_below_pivot":len(below),"bases_at_or_above_pivot":len(above),
        "securities_with_multiple_bases":sum(v>1 for v in per_security.values()),
        "lineages_with_multiple_bases":sum(v>1 for v in per_lineage.values())},
      "distributions":{"distance_to_pivot_pct":_q(distances),"below_pivot_gap_pct":_q(below),
        "bases_per_security":_q(list(per_security.values())),"bases_per_lineage":_q(list(per_lineage.values()))},
      "descriptive_distance_bands_below_pivot":{
        f"within_{b}_pct":sum(0<=x<=b for x in below) for b in bands
      },
      "pattern_counts":dict(sorted(Counter(str(r["pattern_type"]) for r in reps).items())),
      "decision":{"opportunity_rule_defined":False,
        "reason":"Distance bands and cardinalities are descriptive evidence only; no eligibility/lifecycle threshold is selected."}
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("snapshot",type=Path); ap.add_argument("--output",type=Path); a=ap.parse_args()
    rows=[json.loads(x) for x in a.snapshot.read_text().splitlines() if x]
    out=research(rows); body=json.dumps(out,indent=2,sort_keys=True)+"\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(body)
    print(body,end="")
if __name__=="__main__": main()
