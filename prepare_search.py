#!/usr/bin/env python3
"""Prepare/check pinned local browser-search models and matching ONNX Runtime assets.

prepare() may download; check() never uses the network. Neither accesses footage.
"""
from __future__ import annotations
import argparse,concurrent.futures,hashlib,json,os,shutil,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL_LOCK=json.loads('{"embeddings":{"repository":"Xenova/all-MiniLM-L6-v2","revision":"751bff37182d3f1213fa05d7196b954e230abad9","files":[{"path":"config.json","bytes":650,"sha256":null,"git_blob_sha1":"72147e4ff4426ebedbfa2146c4a0999def51a313"},{"path":"tokenizer.json","bytes":711661,"sha256":null,"git_blob_sha1":"c17ed520ed8438736732a54957a69306b8822215"},{"path":"tokenizer_config.json","bytes":366,"sha256":null,"git_blob_sha1":"37fca74771bc76a8e01178ce3a6055a0995f8093"},{"path":"special_tokens_map.json","bytes":125,"sha256":null,"git_blob_sha1":"a8b3208c2884c4efb86e49300fdd3dc877220cdf"},{"path":"vocab.txt","bytes":231508,"sha256":null,"git_blob_sha1":"fb140275c155a9c7c5a3b3e0e77a9e839594a938"},{"path":"onnx/model_quantized.onnx","bytes":22972370,"sha256":"afdb6f1a0e45b715d0bb9b11772f032c399babd23bfc31fed1c170afc848bdb1","git_blob_sha1":null}]},"reranker":{"repository":"Xenova/ms-marco-MiniLM-L-6-v2","revision":"a09144355adeed5f58c8ed011d209bf8ee5a1fec","files":[{"path":"config.json","bytes":824,"sha256":null,"git_blob_sha1":"e94e433dc05771d74530b4a5fdaf8f398da30cab"},{"path":"tokenizer.json","bytes":711396,"sha256":null,"git_blob_sha1":"688882a79f44442ddc1f60d70334a7ff5df0fb47"},{"path":"tokenizer_config.json","bytes":1242,"sha256":null,"git_blob_sha1":"75305659f7795d4549f0e23688b52fa20a32f925"},{"path":"special_tokens_map.json","bytes":125,"sha256":null,"git_blob_sha1":"a8b3208c2884c4efb86e49300fdd3dc877220cdf"},{"path":"vocab.txt","bytes":231508,"sha256":null,"git_blob_sha1":"fb140275c155a9c7c5a3b3e0e77a9e839594a938"},{"path":"quantize_config.json","bytes":722,"sha256":null,"git_blob_sha1":"2f6eece7972c72d198cad373e58d709a0ba266d6"},{"path":"onnx/model_quantized.onnx","bytes":23143499,"sha256":"e9d8ebf845c413e981c175bfe49a3bfa9b3dcce2a3ba54875ee5df5a58639fbe","git_blob_sha1":null}]},"clip":{"repository":"Xenova/clip-vit-base-patch32","revision":"6b7c523703ae26e39be4b03774966f8571c7f523","files":[{"path":"config.json","bytes":4524,"sha256":null,"git_blob_sha1":"e79bad158b04c235740f9b2ec320b17f4030f7a5"},{"path":"tokenizer.json","bytes":2224119,"sha256":null,"git_blob_sha1":"bc1f77d20440541dd073ebae6f6c401087c7d34e"},{"path":"tokenizer_config.json","bytes":775,"sha256":null,"git_blob_sha1":"c9b2a711cbdd039529fa5a66f1965e13eb14451d"},{"path":"preprocessor_config.json","bytes":520,"sha256":null,"git_blob_sha1":"e0675735fd0052745f2f7b7291e4aa7859389998"},{"path":"special_tokens_map.json","bytes":472,"sha256":null,"git_blob_sha1":"2c2130b544c0c5a72d5d00da071ba130a9800fb2"},{"path":"merges.txt","bytes":524619,"sha256":null,"git_blob_sha1":"76e821f1b6f0a9709293c3b6b51ed90980b3166b"},{"path":"vocab.json","bytes":862328,"sha256":null,"git_blob_sha1":"182766ce89b439768edadda342519f33802f5364"},{"path":"onnx/text_model_quantized.onnx","bytes":64504507,"sha256":"73baab855d406190da9faa498cfedf65f15cf309f4cc7385b7b032e6d08e5c3a","git_blob_sha1":null},{"path":"onnx/vision_model_quantized.onnx","bytes":89117001,"sha256":"583fd1110a514667812fee7d684952aaf82a99b959760c8d7dca7e0ab9839299","git_blob_sha1":null}]}}')
ORT_VERSION='1.22.0-dev.20250409-89f8206ba4'
TRANSFORMERS_VERSION='3.8.1'
RUNTIME_LOCK={
 'ort-wasm-simd-threaded.mjs':(20856,'43c25054b6b9ac000f786c65545ff83a45f871e0e310e8c2f4d48a363bb66db4'),
 'ort-wasm-simd-threaded.wasm':(11133407,'f061472c6e77d6d50d079aacdc0ff9b63fee287ddd2cbf46cf62438d3891de2b'),
 'ort-wasm-simd-threaded.jsep.mjs':(44484,'08fb86ec433c78bfb032c5d84a68b8e8e5a8d81268fa39e24314179a5767a5b9'),
 'ort-wasm-simd-threaded.jsep.wasm':(21596019,'c46655e8a94afc45338d4cb2b840475f88e5012d524509916e505079c00bfa39')}
def _sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def _valid(path,spec):
 if not path.is_file():return False,'missing'
 if path.stat().st_size!=spec['bytes']:return False,'size mismatch'
 if spec.get('sha256'):
  return (_sha(path)==spec['sha256'],'SHA256 mismatch')
 data=path.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 return (blob==spec['git_blob_sha1'],'pinned Git blob mismatch')
def _save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name(path.name+'.tmp')
 temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path)
def _download(task):
 root,key,model,spec=task;target=root/'models/.runtime/search-models'/key/spec['path']
 if _valid(target,spec)[0]:return
 target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_name(target.name+'.part')
 url='https://huggingface.co/'+model['repository']+'/resolve/'+model['revision']+'/'+spec['path']+'?download=true'
 last=None
 for attempt in range(4):
  try:
   # Every retry starts a clean partial; completed verified files are reused.
   request=urllib.request.Request(url,headers={'User-Agent':'AIIndexer-prepare-offline/1'})
   with urllib.request.urlopen(request,timeout=60) as response,temp.open('wb') as output:
    shutil.copyfileobj(response,output,length=1024*1024)
   valid,reason=_valid(temp,spec)
   if not valid:raise RuntimeError(f'{key}/{spec["path"]}: {reason}')
   temp.replace(target);return
  except Exception as error:
   last=error;time.sleep(min(2**attempt,8))
 raise RuntimeError(f'Could not prepare {key}/{spec["path"]}: {last}')
def check(root=ROOT,write=True):
 root=Path(root).resolve();models={}
 for key,model in MODEL_LOCK.items():
  files=[];errors=[]
  for spec in model['files']:
   path=root/'models/.runtime/search-models'/key/spec['path'];valid,reason=_valid(path,spec)
   entry={'path':spec['path'],'bytes':spec['bytes'],'ready':valid}
   if valid:entry['sha256']=_sha(path)
   else:entry['error']=reason;errors.append(spec['path']+': '+reason)
   files.append(entry)
  models[key]={'ready':not errors,'repository':model['repository'],'revision':model['revision'],'dtype':'q8','files':files,'errors':errors}
 files=[];errors=[]
 for name,(size,digest) in RUNTIME_LOCK.items():
  path=root/'models/.runtime/browser'/name;valid,reason=_valid(path,{'bytes':size,'sha256':digest})
  files.append({'path':name,'bytes':size,'sha256':digest,'ready':valid})
  if not valid:errors.append(name+': '+reason)
 runtime={'ready':not errors,'transformers_version':TRANSFORMERS_VERSION,'onnxruntime_web_version':ORT_VERSION,'files':files,'errors':errors}
 result={'schema_version':1,'ready':all(x['ready'] for x in models.values()) and runtime['ready'],'models':models,'runtime':runtime,'checked_at':time.time()}
 if write:_save(root/'models/.runtime/search-readiness.json',result)
 return result
def prepare(root=ROOT):
 root=Path(root).resolve()
 status=check(root)
 if status['ready']:return status
 source=root/'viewer/node_modules/onnxruntime-web'
 package=source/'package.json'
 if not package.exists():raise RuntimeError('Install the pinned viewer packages first: npm ci --prefix viewer')
 if json.loads(package.read_text())['version']!=ORT_VERSION:raise RuntimeError('Installed ONNX Runtime version differs from the pinned offline runtime')
 installed=root/'viewer/node_modules/@huggingface/transformers/package.json'
 if not installed.exists() or json.loads(installed.read_text())['version']!=TRANSFORMERS_VERSION:raise RuntimeError('Installed Transformers.js version differs from the pinned frontend')
 target=root/'models/.runtime/browser';target.mkdir(parents=True,exist_ok=True)
 for name,(size,digest) in RUNTIME_LOCK.items():
  src=source/'dist'/name;spec={'bytes':size,'sha256':digest}
  if not _valid(src,spec)[0]:raise RuntimeError('Installed runtime asset failed verification: '+name)
  if not _valid(target/name,spec)[0]:
   temp=target/(name+'.part');shutil.copyfile(src,temp);temp.replace(target/name)
 tasks=[(root,key,model,spec) for key,model in MODEL_LOCK.items() for spec in model['files']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(_download,tasks))
 return check(root)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--check',action='store_true');parser.add_argument('--json',action='store_true')
 args=parser.parse_args();result=check(args.root) if args.check else prepare(args.root)
 if args.json:print(json.dumps(result,indent=2))
 else:
  print('Search assets ready:',result['ready'])
  for key,model in result['models'].items():print(key,model['ready'],model['revision'],model['errors'])
  print('Browser runtime:',result['runtime']['ready'],result['runtime']['errors'])
 return 0 if result['ready'] else 2
if __name__=='__main__':raise SystemExit(main())
