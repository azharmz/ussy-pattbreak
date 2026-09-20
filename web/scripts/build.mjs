import {copyFile,mkdir} from "node:fs/promises";
await mkdir(new URL("../public/d1/",import.meta.url),{recursive:true});
for(const name of ["_worker.js","d1/projector.js","d1/schema.js"])await copyFile(new URL("../"+name,import.meta.url),new URL("../public/"+name,import.meta.url));
console.log("web/public worker sources synchronized");
