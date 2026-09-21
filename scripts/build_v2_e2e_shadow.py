"""Compose existing v2 evidence into an end-to-end shadow reconciliation report."""
import argparse,json
from pathlib import Path
from collections import defaultdict

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--events",required=True); ap.add_argument("--t1",required=True); ap.add_argument("--output",default="audit/v2-e2e-shadow.json"); a=ap.parse_args()
 ev=[json.loads(x) for x in Path(a.events).read_text().splitlines() if x.strip()]; t1=[json.loads(x) for x in Path(a.t1).read_text().splitlines() if x.strip()]
 events=ev
 # event schema preserves contributing assessment ids
 amap={}
 for e in events:
  ids=e.get("contributing_assessment_ids") or e.get("assessment_ids") or []
  for i in ids: amap[str(i)]=e
 exec_events=defaultdict(dict)
 unmatched=0
 for x in t1:
  if x.get("entry_state")!="EXECUTED_T1_OPEN": continue
  e=amap.get(str(x["candidate_id"]))
  if not e: unmatched+=1; continue
  sid=str(x["security_id"]); eid=e.get("event_id") or e.get("breakout_event_id")
  exec_events[sid][eid]={"event_id":eid,"pivot_level":e["pivot_level"],"fill_date":x["fill_date"],"fill_price":x["fill_price"]}
 positions=[]
 for sid,byid in sorted(exec_events.items()):
  es=list(byid.values()); fills={(e["fill_date"],e["fill_price"]) for e in es}
  if len(fills)!=1: raise ValueError(f"economic fill disagreement for {sid}")
  d,p=next(iter(fills)); positions.append({"security_id":sid,"execution_id":f"shadow-execution:{sid}:{d}","position_id":f"shadow-position:{sid}:{d}","entry_date":d,"entry_price":p,"supporting_events":sorted(es,key=lambda z:z["pivot_level"])})
 summary={"event_count":len(events),"mapped_assessment_ids":len(amap),"executed_event_count":sum(len(x["supporting_events"]) for x in positions),"economic_position_count":len(positions),"multi_event_positions":sum(len(x["supporting_events"])>1 for x in positions),"unmatched_executed_assessments":unmatched,"executed_assessments_removed_by_v2":unmatched}
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({"schema":"breakout-v2-e2e-shadow-v1","summary":summary,"positions":positions},indent=2,sort_keys=True)+chr(10));print(json.dumps(summary,sort_keys=True))
if __name__=="__main__":main()
