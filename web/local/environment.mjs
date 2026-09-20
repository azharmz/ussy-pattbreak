import {DatabaseSync} from "node:sqlite";
import {fixtureObjects} from "./fixtures.mjs";
class Prepared{constructor(db,sql){this.db=db;this.sql=sql;this.values=[]}bind(...x){this.values=x;return this}run(){return this.db.prepare(this.sql).run(...this.values)}first(){return this.db.prepare(this.sql).get(...this.values)??null}all(){return{results:this.db.prepare(this.sql).all(...this.values)}}}
class D1{constructor(){this.db=new DatabaseSync(":memory:");this.db.exec("PRAGMA foreign_keys=ON")}prepare(sql){return new Prepared(this.db,sql)}batch(q){this.db.exec("BEGIN");try{const x=q.map(s=>s.run());this.db.exec("COMMIT");return x}catch(e){this.db.exec("ROLLBACK");throw e}}}
class R2Object{constructor(b){this.b=b}json(){return Promise.resolve(JSON.parse(this.b))}arrayBuffer(){return Promise.resolve(this.b.buffer.slice(this.b.byteOffset,this.b.byteOffset+this.b.byteLength))}}
export function localEnvironment(){const objects=fixtureObjects();return{DB:new D1,R2_BUCKET:{get:key=>Promise.resolve(objects.has(key)?new R2Object(objects.get(key)):null)},LOCAL_FIXTURE:"1",ASSETS:{fetch:()=>new Response("not found",{status:404})}}}
