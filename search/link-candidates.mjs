// Bounded metadata-link candidates from the SAME native Orama CLIP512 schema.
import * as orama from '@orama/orama';
import {createProjectIndexes,clipCandidates} from './orama_projection.mjs';
import {readFile,realpath} from 'node:fs/promises';
import {dirname,resolve,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
async function main(){
 const a=process.argv.slice(2),arg=k=>{const i=a.indexOf(k);return i<0?null:a[i+1];};
 if(!arg('--project')||!arg('--content-id'))throw Error('Required: --project LAB_PROJECT --content-id SHA --eligible JSON_ARRAY');
 const project=await realpath(arg('--project'));
 if(project===ROOT)throw Error('Application folder is not a media project');
 const notes=resolve(project,'_DIT_NOTES');
 const fingerprints=JSON.parse(await readFile(resolve(notes,'clip-fingerprints.json'),'utf8'));
 const eligible=JSON.parse(arg('--eligible')||'[]');if(!Array.isArray(eligible))throw Error('Eligible content IDs must be an array');
 let projection={documents:[]};try{const c=JSON.parse(await readFile(resolve(notes,'catalog.json'),'utf8'));projection=c.search_projection||projection;}catch(e){if(e.code!=='ENOENT')throw e;}
 const indexes=createProjectIndexes(orama,projection);
 const candidates=await clipCandidates(orama,indexes,arg('--content-id'),fingerprints,eligible,{limit:Number(arg('--limit')||3),threshold:Number(arg('--threshold')||.9)});
 process.stdout.write(JSON.stringify({candidates})+'\n');
}
main().catch(e=>{process.stderr.write(e.message+'\n');process.exitCode=1;});
