import {normalizeCatalog,buildDocuments} from '../src/data.js';
const origin=process.argv[2]||'http://127.0.0.1:8765';
const networkFetch=globalThis.fetch;
const catalog=normalizeCatalog(await (await networkFetch(origin+'/api/catalog')).json());
const readiness=await (await networkFetch(origin+'/api/readiness')).json();
if(readiness.backend?.type!=='mlx'||!readiness.backend.ready)throw new Error('MLX backend not ready');
globalThis.fetch=(url,options)=>networkFetch(new URL(url,origin),options);
let resolveReady,resolveResult;const ready=new Promise(r=>resolveReady=r);let current=0;
globalThis.self={postMessage:m=>{if(m.type==='status'&&m.phase==='ready')resolveReady();if(m.type==='results'&&m.id===current&&['reranked','images'].includes(m.stage))resolveResult(m);}};
await import('../src/search.worker.js');
self.onmessage({data:{type:'init',documents:buildDocuments(catalog),projectId:catalog.project.id,readiness}});await ready;
const output=[];
for(const [mode,query] of [['text','chocolate'],['text','vehicle'],['text','forest'],['text','endangered ecosystem'],['images','chocolate'],['images','bison'],['images','sunset']]){
 const result=new Promise(r=>resolveResult=r);self.onmessage({data:{type:'query',id:++current,mode,query}});const found=await result;output.push({mode,query,stage:found.stage,results:found.results.map(r=>({seconds:r.seconds,text:r.text,score:mode==='images'?r.score:r.rerankScore}))});
}
console.log(JSON.stringify(output,null,2));
