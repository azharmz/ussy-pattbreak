import {SCHEMA} from "./schema.js";
export const VERSION="dashboard-projection-v11";
export const POINTERS={candidates:"pattern-breakout/production/candidates/current.json",t1:"pattern-breakout/production/t1-execution/current.json",lifecycle:"pattern-breakout/production/lifecycle/current.json",prices:"pattern-breakout/production/dashboard-prices/current.json"};
const req=(x,k)=>{if(x?.[k]===undefined||x[k]===null||x[k]==="")throw Error("missing "+k);return x[k]};
async function object(env,key){const x=await env.R2_BUCKET.get(key);if(!x)throw Error("missing R2 object: "+key);return x}
export async function readPointers(env){return Object.fromEntries(await Promise.all(Object.entries(POINTERS).map(async([stage,key])=>{const p=await(await object(env,key)).json();["jsonl_key","metadata_key","source_hash","as_of_date"].forEach(k=>req(p,k));return[stage,p]})))}
export async function ensureSchema(db){await db.batch(SCHEMA.map(x=>db.prepare(x)))}
export async function currentRun(db){const x=await db.prepare("SELECT payload FROM dashboard_current WHERE singleton=1").first();return x?JSON.parse(x.payload):null}
export async function validCurrent(db,run){if(!run||run.schema_version!==VERSION)return false;const c=await db.prepare("SELECT (SELECT COUNT(*) FROM dashboard_opportunities_v8 WHERE generation=?) opportunities,(SELECT COUNT(*) FROM dashboard_positions_v8 WHERE generation=?) positions").bind(run.generation,run.generation).first();return c.opportunities===run.opportunities&&c.positions===run.positions}
