import {SCHEMA} from "./schema.js";
export const VERSION="dashboard-projection-v12";
const CURRENT="pattern-breakout/production/dashboard-v2/current.json",PRICE="pattern-breakout/production/dashboard-prices/current.json";
const req=(x,k)=>{if(x?.[k]===undefined||x[k]===null||x[k]==="")throw Error("missing "+k);return x[k]};
async function object(env,key){const x=await env.R2_BUCKET.get(key);if(!x)throw Error("missing R2 object: "+key);return x}
export async function readPointers(env){const m=await(await object(env,CURRENT)).json();if(m.schema_version!=="dashboard-v2-current-v1")throw Error("invalid dashboard v2 current manifest");const signal=req(m,"signal_date"),out={};for(const k of ["events","execution","lifecycle"]){const p=req(m.stages,k);["jsonl_key","metadata_key","source_hash","signal_date"].forEach(x=>req(p,x));if(p.signal_date!==signal)throw Error("dashboard v2 current cohort mismatch");out[k]={...p,as_of_date:p.signal_date}}const price=await(await object(env,PRICE)).json();["jsonl_key","metadata_key","source_hash","as_of_date"].forEach(x=>req(price,x));out.prices=price;return out}
export async function ensureSchema(db){await db.batch(SCHEMA.map(x=>db.prepare(x)))}
export async function currentRun(db){const x=await db.prepare("SELECT payload FROM dashboard_current WHERE singleton=1").first();return x?JSON.parse(x.payload):null}
export async function validCurrent(db,run){if(!run||run.schema_version!==VERSION)return false;const c=await db.prepare("SELECT (SELECT COUNT(*) FROM dashboard_opportunities_v8 WHERE generation=?) opportunities,(SELECT COUNT(*) FROM dashboard_positions_v8 WHERE generation=?) positions").bind(run.generation,run.generation).first();return c.opportunities===run.opportunities&&c.positions===run.positions}
