#!/usr/bin/env node
// Copy only the ORT assets belonging to the pinned installed package. No CDN.
import {createRequire} from 'node:module';
import {dirname,resolve,join} from 'node:path';
import {mkdir,copyFile,readdir} from 'node:fs/promises';
const require=createRequire(import.meta.url);
const packagePath=require.resolve('onnxruntime-web/package.json');
const source=join(dirname(packagePath),'dist');
const destination=resolve(process.argv[2]||'public/runtime');
await mkdir(destination,{recursive:true});
const files=(await readdir(source)).filter(n=>/^ort-wasm.*\.(wasm|mjs)$/.test(n));
for(const name of files)await copyFile(join(source,name),join(destination,name));
console.log(JSON.stringify({source,destination,files},null,2));
