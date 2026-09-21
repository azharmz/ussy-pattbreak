"""Audit whether assessment-level T1 rows fan out into duplicate security positions."""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output",default="audit/t1-position-identity.json"); a=ap.parse_args()
    p=Path(a.input_dir)/"t1-execution.jsonl"; rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    executed=[x for x in rows if x["entry_state"]=="EXECUTED_T1_OPEN"]
    bysec=defaultdict(list); bypivot=defaultdict(list)
    for x in executed:
        sid=str(x["security_id"]); bysec[sid].append(x); bypivot[(sid,float(x["pivot_level"]))].append(x)
    sec_summary=[]
    for sid,xs in sorted(bysec.items()):
        piv=sorted({float(x["pivot_level"]) for x in xs})
        sec_summary.append({"security_id":sid,"executed_rows":len(xs),"executed_pivot_count":len(piv),"executed_pivots":piv,
          "fill_dates":sorted({x["fill_date"] for x in xs}),"fill_prices":sorted({x["fill_price"] for x in xs})})
    summary={"t1_rows":len(rows),"executed_assessment_rows":len(executed),"executed_unique_securities":len(bysec),
      "executed_unique_security_pivots":len(bypivot),
      "securities_with_multiple_executed_rows":sum(len(v)>1 for v in bysec.values()),
      "securities_with_multiple_executed_pivots":sum(len({float(x["pivot_level"]) for x in v})>1 for v in bysec.values()),
      "assessment_row_excess_over_security_positions":len(executed)-len(bysec),
      "assessment_row_excess_over_pivot_events":len(executed)-len(bypivot),
      "entry_state_counts":dict(Counter(x["entry_state"] for x in rows))}
    payload={"schema":"t1-position-identity-audit-v1","summary":summary,"securities":sec_summary}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2,sort_keys=True)+chr(10))
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
