"""Collapse executable v2 events into one economic security execution and position."""
import argparse,hashlib,json
from collections import defaultdict
from dataclasses import asdict
from datetime import date,datetime,timezone
from pathlib import Path
from pattern_breakout.entry_v2 import BreakoutEventEntry,EventEntryState
from pattern_breakout.execution_v2 import arbitrate_security_execution
from pattern_breakout.lifecycle_v2 import open_from_security_execution
VERSION="pattern-breakout-security-execution-checkpoint-v2"
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input-dir",default="upstream");ap.add_argument("--output-dir",default="checkpoints");a=ap.parse_args()
 inp=Path(a.input_dir);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 meta=json.loads((inp/"t1-event-execution-v2.json").read_text());raw=(inp/"t1-event-execution-v2.jsonl").read_bytes()
 if hashlib.sha256(raw).hexdigest()!=meta["source_hash"].removeprefix("sha256:"):raise ValueError("T1 event checkpoint checksum mismatch")
 groups=defaultdict(list)
 for line in raw.decode().splitlines():
  x=json.loads(line)
  if x["entry_state"]!="EXECUTED_T1_OPEN":continue
  e=BreakoutEventEntry(event_id=x["event_id"],security_id=str(x["security_id"]),signal_date=date.fromisoformat(x["signal_date"]),pivot_level=float(x["pivot_level"]),next_session_date=date.fromisoformat(x["next_session_date"]) if x["next_session_date"] else None,next_open=x["next_open"],buy_zone_floor=x["buy_zone_floor"],buy_zone_ceiling=x["buy_zone_ceiling"],open_extension_pct=x["open_extension_pct"],entry_state=EventEntryState(x["entry_state"]),fill_date=date.fromisoformat(x["fill_date"]) if x["fill_date"] else None,fill_price=x["fill_price"],fill_source=x["fill_source"],entry_version=x["entry_version"])
  groups[(e.security_id,e.signal_date)].append(e)
 executions=[];positions=[]
 for _,xs in sorted(groups.items()):
  ex=arbitrate_security_execution(xs)
  if ex is None:continue
  ey=asdict(ex);ey["signal_date"]=ey["signal_date"].isoformat();ey["fill_date"]=ey["fill_date"].isoformat();ey["supporting_event_ids"]=list(ey["supporting_event_ids"]);ey["supporting_pivots"]=list(ey["supporting_pivots"]);executions.append(ey)
  p=open_from_security_execution(ex);py=asdict(p);py["entry_date"]=py["entry_date"].isoformat();py["supporting_event_ids"]=list(py["supporting_event_ids"]);py["supporting_pivots"]=list(py["supporting_pivots"]);positions.append(py)
 ep="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in executions);pp="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in positions)
 signal=meta["signal_date"];common={"signal_date":signal,"upstream_t1_event_hash":meta["source_hash"],"created_at":datetime.now(timezone.utc).isoformat()}
 em={**common,"stage":"security-execution-v2","schema_version":"pattern-breakout-security-execution-v2","contract_version":VERSION,"source_hash":"sha256:"+hashlib.sha256(ep.encode()).hexdigest(),"summary":{"execution_count":len(executions),"multi_event_execution_count":sum(len(x["supporting_event_ids"])>1 for x in executions)}}
 pm={**common,"stage":"lifecycle-v2","schema_version":"pattern-breakout-position-v2","contract_version":"pattern-breakout-position-v2","upstream_security_execution_hash":em["source_hash"],"source_hash":"sha256:"+hashlib.sha256(pp.encode()).hexdigest(),"summary":{"position_count":len(positions),"open_count":len(positions)}}
 for name,obj,payload in [("security-execution-v2",em,ep),("lifecycle-v2",pm,pp)]:
  (out/(name+".json")).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n");(out/(name+".jsonl")).write_text(payload)
 print(json.dumps({"executions":em["summary"],"positions":pm["summary"]},sort_keys=True))
if __name__=="__main__":main()
