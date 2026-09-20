export const POINTERS={
 morphology:"pattern-breakout/production/morphology/current.json",
 candidates:"pattern-breakout/production/candidates/current.json",
 t1:"pattern-breakout/production/t1-execution/current.json",
 lifecycle:"pattern-breakout/production/lifecycle/current.json",
};

const dec=new TextDecoder();
const sha256=async bytes=>"sha256:"+[...new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))].map(x=>x.toString(16).padStart(2,"0")).join("");
const parseLines=bytes=>dec.decode(bytes).split(/\r?\n/).filter(Boolean).map(JSON.parse);

async function object(env,key){
 const o=await env.R2_BUCKET.get(key); if(!o)throw Error("missing R2 object: "+key); return o;
}
async function loadStage(env,pointerKey){
 const p=await (await object(env,pointerKey)).json();
 if(!p.jsonl_key||!p.metadata_key||!p.source_hash)throw Error("invalid pointer: "+pointerKey);
 const [data,metaObj]=await Promise.all([object(env,p.jsonl_key),object(env,p.metadata_key)]);
 const bytes=await data.arrayBuffer(), actual=await sha256(bytes), meta=await metaObj.json();
 if(actual!==p.source_hash)throw Error("checksum mismatch: "+pointerKey);
 const mh=meta.source_hash; if(mh && mh!==actual && mh!==actual.replace("sha256:",""))throw Error("metadata hash mismatch: "+pointerKey);
 return {pointer:p,meta,rows:parseLines(bytes),hash:actual};
}
const id=(...x)=>x.filter(v=>v!=null).join(":");
const dist=(close,pivot)=>close==null||pivot==null?null:(Number(close)/Number(pivot)-1)*100;

export async function buildProjection(env){
 const [m,c,t,l]=await Promise.all(Object.values(POINTERS).map(k=>loadStage(env,k)));
 const candidate=new Map(c.rows.map(x=>[x.candidate_id,x]));
 const t1=new Map(t.rows.map(x=>[x.candidate_id,x]));
 const opportunity=[];
 for(const x of m.rows){
  // Core contract: PatternBreakoutCandidate.candidate_id is exactly the frozen
  // morphology assessment_id. Never fuzzy-match by ticker/date/pivot.
  const cc=candidate.get(x.assessment_id)||null;
  if(cc && (String(cc.security_id)!==String(x.security_id) || cc.signal_date!==x.asof_date))
    throw Error("candidate/morphology identity mismatch: "+x.assessment_id);
  const tt=cc?t1.get(cc.candidate_id)||null:null;
  if(tt && String(tt.security_id)!==String(x.security_id))
    throw Error("T1/candidate identity mismatch: "+x.assessment_id);
  opportunity.push({...x,breakout:cc,t1:tt});
 }
 return {stages:{m,c,t,l},opportunities:opportunity,positions:l.rows};
}

export async function syncProjection(env){
 const p=await buildProjection(env), asof=p.stages.l.pointer.as_of_date;
 const runId=id("projection",asof,p.stages.m.hash,p.stages.c.hash,p.stages.t.hash,p.stages.l.hash);
 await env.DB.prepare("INSERT OR REPLACE INTO projection_runs(run_id,as_of_date,ready_source_hash,morphology_source_hash,candidate_source_hash,t1_source_hash,lifecycle_source_hash,engine_version,schema_version,producer_commit,created_at,projected_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,datetime('now'))")
  .bind(runId,asof,p.stages.m.meta.upstream_frozen_ready?.source_hash||null,p.stages.m.hash,p.stages.c.hash,p.stages.t.hash,p.stages.l.hash,p.stages.m.meta.engine_version||"33-core-p8-frozen-v1","dashboard-projection-v1",null,p.stages.l.meta.created_at||new Date().toISOString()).run();
 const ob=env.DB.batch.bind(env.DB);
 const ops=[];
 for(const q of p.opportunities){
  const b=q.breakout,t=q.t1, close=b?.close??null;
  ops.push(env.DB.prepare("INSERT OR REPLACE INTO opportunities(assessment_id,base_id,lineage_id,security_id,ticker,pattern_type,morphology_status,native_state,candidate_semantics,structural_start,structural_end,pivot_source_date,pivot_level,depth_pct,as_of_date,as_of_close,distance_to_pivot_pct,breakout_state,breakout_close,volume_ratio,signal_date,t1_open,open_extension_pct,t1_status,entry_date,entry_price,source_hash,projection_run_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
   .bind(q.assessment_id,q.base_id,q.lineage_id,String(q.security_id),q.ticker,q.pattern,q.normalized_status,q.native_state,q.candidate_semantics,q.structural_start,q.structural_end,q.pivot_source_date,q.pivot_level,q.depth_pct,q.asof_date,close,dist(close,q.pivot_level),b?.breakout_state||"PIVOT_NOT_CROSSED",close,b?.breakout_volume_ratio??null,b?.signal_date??null,t?.next_open??null,t?.open_extension_pct??null,t?.entry_state??null,t?.fill_date??null,t?.fill_price??null,p.stages.m.hash,runId));
 }
 for(let i=0;i<ops.length;i+=80)await env.DB.batch(ops.slice(i,i+80));
 const pos=[];
 for(const x of p.positions)pos.push(env.DB.prepare("INSERT OR REPLACE INTO positions(position_id,candidate_id,security_id,pivot_level,entry_date,entry_price,state,exit_signal_date,exit_reason,exit_date,exit_price,eight_week_first_rapid_winner_date,last_evaluated_date,as_of_date,source_hash,projection_run_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").bind(x.position_id,x.candidate_id,String(x.security_id),x.pivot_level,x.entry_date,x.entry_price,x.state,x.exit_signal_date,x.exit_reason,x.exit_date,x.exit_price,x.eight_week_first_rapid_winner_date,x.last_evaluated_date,asof,p.stages.l.hash,runId));
 for(let i=0;i<pos.length;i+=80)await env.DB.batch(pos.slice(i,i+80));
 return {run_id:runId,as_of_date:asof,opportunities:ops.length,positions:pos.length};
}
