import {syncProjection} from "./d1/projector.js";
const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});

async function health(db){
 const run=await db.prepare("SELECT * FROM projection_runs ORDER BY as_of_date DESC, projected_at DESC LIMIT 1").first();
 const states=await db.prepare("SELECT state, COUNT(*) count FROM positions GROUP BY state").all();
 return {status:run?"READY":"EMPTY",latest_projection:run||null,position_states:states.results||[]};
}
async function opportunities(db,url){
 const state=url.searchParams.get("breakout_state"); const limit=Math.min(Number(url.searchParams.get("limit")||100),500);
 let sql="SELECT * FROM opportunities WHERE morphology_status='RECOGNIZED'",bind=[];
 if(state){sql+=" AND breakout_state=?";bind.push(state)}
 sql+=" ORDER BY as_of_date DESC, ABS(COALESCE(distance_to_pivot_pct,999999)) ASC LIMIT ?";bind.push(limit);
 return (await db.prepare(sql).bind(...bind).all()).results;
}
async function positions(db,url){
 const state=url.searchParams.get("state"); const limit=Math.min(Number(url.searchParams.get("limit")||100),500);
 let sql="SELECT * FROM positions",bind=[]; if(state){sql+=" WHERE state=?";bind.push(state)}
 sql+=" ORDER BY as_of_date DESC, ticker ASC LIMIT ?";bind.push(limit);
 return (await db.prepare(sql).bind(...bind).all()).results;
}
async function history(db,url){
 const limit=Math.min(Number(url.searchParams.get("limit")||100),500);
 return (await db.prepare("SELECT * FROM positions WHERE state='CLOSED' ORDER BY exit_date DESC LIMIT ?").bind(limit).all()).results;
}
async function detail(db,id){
 const opportunity=await db.prepare("SELECT * FROM opportunities WHERE assessment_id=?").bind(id).first();
 if(!opportunity)return null;
 const evidence=(await db.prepare("SELECT * FROM opportunity_evidence WHERE assessment_id=? ORDER BY as_of_date DESC, extension_type").bind(id).all()).results;
 return {opportunity,evidence};
}
export default {async fetch(request,env){
 const url=new URL(request.url); const p=url.pathname;
 try{
  if(p==="/api/admin/sync" && request.method==="POST"){if(request.headers.get("authorization")!==`Bearer ${env.SYNC_TOKEN}`)return json({error:"unauthorized"},401);return json(await syncProjection(env));}
  if(p==="/api/health")return json(await health(env.DB));
  if(p==="/api/opportunities")return json(await opportunities(env.DB,url));
  if(p.startsWith("/api/opportunities/")){const x=await detail(env.DB,decodeURIComponent(p.split("/").pop()));return x?json(x):json({error:"not_found"},404)}
  if(p==="/api/positions")return json(await positions(env.DB,url));
  if(p==="/api/history")return json(await history(env.DB,url));
  return env.ASSETS.fetch(request);
 }catch(e){return json({error:"serving_error",message:String(e&&e.message||e)},500)}
}};
