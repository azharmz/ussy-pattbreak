import {createHash} from "node:crypto";
const iso=x=>x.toISOString().slice(0,10), signal=new Date("2026-09-17T00:00:00Z"), execution="2026-09-18";
export function fixtureRows(){
 const candidates=[],t1=[],lifecycle=[];
 for(let i=0;i<426;i++){
  const id=`assessment:${String(i+1).padStart(4,"0")}`,security=String(100000+i),pivot=100+i/10,pattern=["CUP_WITH_HANDLE","CUP_WITHOUT_HANDLE","DOUBLE_BOTTOM","FLAT_BASE"][i%4];
  candidates.push({candidate_id:id,security_id:security,signal_date:iso(signal),pattern_type:pattern,pivot_level:pivot,breakout_volume_ratio:1.4+(i%9)/10,pivot_crossed:true,breakout_state:"TECHNICAL_BREAKOUT_CANDIDATE",candidate_stage:"TECHNICAL_BREAKOUT_CANDIDATE",breakout_version:"pattern-breakout-confirmation-v1",morphology_schema:"oneil-pattern-output-v2",morphology_engine:"33-core-p8-frozen-v1"});
  const entry=i<211?"EXECUTED_T1_OPEN":i<306?"BELOW_PIVOT_AT_OPEN":"MISSED_EXTENDED_AT_OPEN",fill=entry==="EXECUTED_T1_OPEN"?execution:null,price=entry==="EXECUTED_T1_OPEN"?pivot*1.02:null;
  t1.push({candidate_id:id,security_id:security,signal_date:iso(signal),candidate_stage:"TECHNICAL_BREAKOUT_CANDIDATE",pivot_level:pivot,next_session_date:execution,next_open:price??(entry==="BELOW_PIVOT_AT_OPEN"?pivot*.99:pivot*1.06),open_extension_pct:price?0.02:null,entry_state:entry,fill_date:fill,fill_price:price,fill_source:fill?"DAILY_OHLCV_OPEN":null});
  const state=i<178?"OPEN":i<211?"EXIT_PENDING":"NOT_OPENED";
  lifecycle.push({position_id:`position:${id}`,candidate_id:id,security_id:security,entry_date:fill,entry_price:price,pivot_level:pivot,state,exit_signal_date:state==="EXIT_PENDING"?execution:null,exit_reason:state==="EXIT_PENDING"?(i<182?"DEFENSIVE_LOSS":"TEN_WEEK_MA_VIOLATION"):null,exit_date:null,exit_price:null,lifecycle_version:"pattern-breakout-lifecycle-v1"});
 }
 return{candidates,t1,lifecycle};
}
const bytes=x=>Buffer.from(x.map(r=>JSON.stringify(r)).join("\n")+"\n"),sha=b=>"sha256:"+createHash("sha256").update(b).digest("hex");
export function fixtureObjects(){const rows=fixtureRows(),objects=new Map;const membership={snapshot_date:"2026-08-28",count:426,records:rows.candidates.map((x,i)=>({security_id:x.security_id,ticker:`T${String(i+1).padStart(4,"0")}`}))};objects.set("universe/membership/2026-08-28.json",Buffer.from(JSON.stringify(membership)));objects.set("universe/current.json",Buffer.from(JSON.stringify({snapshot_date:"2026-08-28",membership_key:"universe/membership/2026-08-28.json"})));for(const[stage,data]of Object.entries(rows)){const path=stage==="t1"?"t1-execution":stage,key=`fixture/${path}.jsonl`,mkey=`fixture/${path}.json`,body=bytes(data),source_hash=sha(body),as_of_date=stage==="candidates"?"2026-09-17":"2026-09-18",meta={source_hash,created_at:"2026-09-18T00:00:00Z"};if(stage==="t1")meta.upstream_candidate_hash=sha(bytes(rows.candidates));objects.set(key,body);objects.set(mkey,Buffer.from(JSON.stringify(meta)));objects.set(`pattern-breakout/production/${path}/current.json`,Buffer.from(JSON.stringify({jsonl_key:key,metadata_key:mkey,source_hash,as_of_date})));}return objects}
