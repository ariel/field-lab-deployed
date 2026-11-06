#!/usr/bin/env python3
"""Prepare pinned MiniLM weights for the established mlx-vlm BERT loaders; check is offline."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import time
ROOT=Path(__file__).resolve().parent
LOCK={
 'text':{'repository':'sentence-transformers/all-MiniLM-L6-v2','revision':'1110a243fdf4706b3f48f1d95db1a4f5529b4d41','files':[
  ('1_Pooling/config.json',190,'d1514c3162bbe87b343f565fadc62e6c06f04f03'),
  ('config.json',612,'72b987fd805cfa2b58c4c8c952b274a11bfd5a00'),
  ('model.safetensors',90868376,'53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db'),
  ('sentence_bert_config.json',53,'59d594003bf59880a884c574bf88ef7555bb0202'),
  ('special_tokens_map.json',112,'e7b0375001f109a6b8873d756ad4f7bbb15fbaa5'),
  ('tokenizer.json',466247,'cb202bfe2e3c98645018a6d12f182a434c9d3e02'),
  ('tokenizer_config.json',350,'c79f2b6a0cea6f4b564fed1938984bace9d30ff0'),
  ('vocab.txt',231508,'fb140275c155a9c7c5a3b3e0e77a9e839594a938')]},
 'reranker':{'repository':'cross-encoder/ms-marco-MiniLM-L6-v2','revision':'233902d25c440f23af6f7d6e94d2946bac0bee0a','files':[
  ('config.json',794,'88bc4f74b33a2073abc9a66cb532b889448ac3ed'),
  ('model.safetensors',90870598,'821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae'),
  ('special_tokens_map.json',132,'7520992f25914d962f0e2fd0e0566fc33d19ec59'),
  ('tokenizer.json',711396,'688882a79f44442ddc1f60d70334a7ff5df0fb47'),
  ('tokenizer_config.json',1330,'a2435fedfac32b9ad70f052d4f84007730cd3109'),
  ('vocab.txt',231508,'fb140275c155a9c7c5a3b3e0e77a9e839594a938')]}}


def _hash(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def _valid(path,spec):
    _,size,expected=spec
    if not path.is_file() or path.stat().st_size!=size:return False
    if len(expected)==64:return _hash(path)==expected
    data=path.read_bytes()
    return hashlib.sha1(b'blob '+str(size).encode()+b'\0'+data).hexdigest()==expected


def _save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);part=path.with_suffix(path.suffix+'.tmp')
    part.write_text(json.dumps(data,indent=2)+'\n');part.replace(path)


def check(root=ROOT,write=False):
    root=Path(root).resolve();models={}
    for kind,spec in LOCK.items():
        files=[]
        for item in spec['files']:
            path=root/'models/mlx-search'/kind/item[0];valid=_valid(path,item)
            files.append({'path':item[0],'bytes':item[1],'ready':valid,'sha256':_hash(path) if valid else None})
        models[kind]={'ready':all(f['ready'] for f in files),'repository':spec['repository'],'revision':spec['revision'],'files':files}
    result={'schema_version':1,'ready':all(m['ready'] for m in models.values()),
            'revision':{key:value['revision'] for key,value in LOCK.items()},'models':models,
            'runtime':'mlx-vlm 0.7.11 established BERT embedding and sequence-classifier loaders','dimensions':384,
            'pooling':'attention-mask mean, L2 normalized','reranker_output':'raw single-label logits, higher is more relevant',
            'checked_at':time.time()}
    if write:_save(root/'models/.runtime/mlx-text-readiness.json',result)
    return result


def _download(item):
    root,kind,spec,file=item;name,size,digest=file;path=root/'models/mlx-search'/kind/name
    if _valid(path,file):return
    path.parent.mkdir(parents=True,exist_ok=True);part=path.with_name(path.name+'.part')
    url='https://huggingface.co/'+spec['repository']+'/resolve/'+spec['revision']+'/'+name+'?download=true'
    request=urllib.request.Request(url,headers={'User-Agent':'DITNotes-prepare-mlx-text/1'})
    with urllib.request.urlopen(request,timeout=120) as incoming,part.open('wb') as outgoing:shutil.copyfileobj(incoming,outgoing,length=1024*1024)
    if not _valid(part,file):raise RuntimeError('Pinned model checksum failed: '+kind+'/'+name)
    part.replace(path)


def prepare(root=ROOT):
    root=Path(root).resolve()
    jobs=[(root,kind,spec,item) for kind,spec in LOCK.items() for item in spec['files']]
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(_download,jobs))
    result=check(root,write=True)
    if not result['ready']:raise RuntimeError('MLX text model verification incomplete')
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result=check(args.root,write=True) if args.check else prepare(args.root)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['ready'] else 1)
