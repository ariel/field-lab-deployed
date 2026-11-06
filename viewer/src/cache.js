const DB='fieldnotes-semantic-v1', STORE='vectors';
let database;
export function openCache(){
  if(database)return database;
  database=new Promise((resolve,reject)=>{const r=indexedDB.open(DB,1);r.onupgradeneeded=()=>r.result.createObjectStore(STORE);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
  return database;
}
export async function cacheGet(key){const db=await openCache();return new Promise((resolve,reject)=>{const r=db.transaction(STORE).objectStore(STORE).get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
export async function cachePut(key,value){const db=await openCache();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(value,key);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);});}
export async function contentKey(projectId,doc,revision="unspecified"){
  const input=`all-MiniLM-L6-v2:${revision}:q8:transformers3.8.1:mean-normalized:v1\0${doc.kind}\0${doc.text}`;
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(input));
  const hash=Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');
  return `${projectId}:${doc.contentId}:${hash}`;
}

export async function imageKey(projectId,doc,revision="unspecified"){
  const value=`clip-vit-base-patch32:${revision}:q8:transformers3.8.1:normalized:v1\0${doc.image}\0${doc.seconds}`;
  const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));
  return `${projectId}:${doc.contentId}:image:${Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('')}`;
}
