"""Open lifecycle positions strictly from an immutable T1_EXECUTION checkpoint."""
from __future__ import annotations
import argparse, hashlib, json, os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from pattern_breakout.entry_v1 import PatternBreakoutEntry, EntryState
from pattern_breakout.lifecycle_v1 import open_from_entry

VERSION="pattern-breakout-open-position-checkpoint-v1"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="upstream"); ap.add_argument("--output-dir",default="checkpoints"); a=ap.parse_args()
    inp=Path(a.input_dir); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((inp/"t1-execution.json").read_text()); raw=(inp/"t1-execution.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=meta["source_hash"].removeprefix("sha256:"): raise ValueError("T1 checkpoint checksum mismatch")
    rows=[]; counts={}
    for line in raw.decode().splitlines():
        x=json.loads(line)
        e=PatternBreakoutEntry(candidate_id=x["candidate_id"],security_id=str(x["security_id"]),signal_date=date.fromisoformat(x["signal_date"]),candidate_stage=x["candidate_stage"],pivot_level=x["pivot_level"],next_session_date=date.fromisoformat(x["next_session_date"]) if x["next_session_date"] else None,next_open=x["next_open"],buy_zone_floor=x["buy_zone_floor"],buy_zone_ceiling=x["buy_zone_ceiling"],open_extension_pct=x["open_extension_pct"],entry_state=EntryState(x["entry_state"]),fill_date=date.fromisoformat(x["fill_date"]) if x["fill_date"] else None,fill_price=x["fill_price"],fill_source=x["fill_source"],entry_version=x["entry_version"])
        p=open_from_entry(e); y=asdict(p); y["entry_date"]=y["entry_date"].isoformat() if y["entry_date"] else None; y["exit_signal_date"]=None; y["exit_date"]=None; y["state"]=y["state"].value
        rows.append(y); counts[y["state"]]=counts.get(y["state"],0)+1
    payload="".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows); digest=hashlib.sha256(payload.encode()).hexdigest()
    m={"stage":"lifecycle","schema_version":"pattern-breakout-position-v1","contract_version":VERSION,"source_identity":f"t1-execution:{meta['source_hash']}","source_hash":f"sha256:{digest}","created_at":datetime.now(timezone.utc).isoformat(),"producer_commit":os.getenv("GITHUB_SHA","local"),"producer_run":os.getenv("GITHUB_RUN_ID","local"),"upstream_t1_hash":meta["source_hash"],"summary":{"position_count":len(rows),"state_counts":counts}}
    (out/"open-positions.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n"); (out/"open-positions.jsonl").write_text(payload)
    print(json.dumps(m["summary"],sort_keys=True))
if __name__=="__main__": main()
