"""Audit multi-pivot T1 executions to design security-level position arbitration."""
import argparse,json
from collections import defaultdict
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output",default="audit/t1-multipivot-arbitration.json"); a=ap.parse_args()
    rows=[json.loads(x) for x in (Path(a.input_dir)/"t1-execution.jsonl").read_text().splitlines() if x.strip()]
    ex=[x for x in rows if x["entry_state"]=="EXECUTED_T1_OPEN"]
    bysec=defaultdict(list)
    for x in ex: bysec[str(x["security_id"])].append(x)
    securities=[]
    for sid,xs in sorted(bysec.items()):
        pivots=sorted({float(x["pivot_level"]) for x in xs})
        if len(pivots)<=1: continue
        fills=sorted({float(x["fill_price"]) for x in xs if x["fill_price"] is not None})
        dates=sorted({x["fill_date"] for x in xs if x["fill_date"]})
        per=[]
        for p in pivots:
            ps=[x for x in xs if float(x["pivot_level"])==p]
            fill=float(ps[0]["fill_price"])
            per.append({"pivot_level":p,"assessment_execution_rows":len(ps),"fill_price":fill,
              "t1_extension_pct":fill/p-1.0,"buy_zone_ceiling":p*1.05})
        securities.append({"security_id":sid,"executed_assessment_rows":len(xs),"executed_pivot_count":len(pivots),
          "fill_prices":fills,"fill_dates":dates,"same_fill_price":len(fills)==1,"same_fill_date":len(dates)==1,
          "pivots":per})
    summary={"multi_executed_pivot_securities":len(securities),
      "all_same_fill_price":all(x["same_fill_price"] for x in securities),
      "all_same_fill_date":all(x["same_fill_date"] for x in securities),
      "total_executed_pivot_events":sum(x["executed_pivot_count"] for x in securities),
      "total_assessment_execution_rows":sum(x["executed_assessment_rows"] for x in securities),
      "max_executed_pivots_per_security":max((x["executed_pivot_count"] for x in securities),default=0)}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({"schema":"t1-multipivot-arbitration-audit-v1","summary":summary,"securities":securities},indent=2,sort_keys=True)+chr(10))
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
