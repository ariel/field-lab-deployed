"""Pinned, checksum-verified model preparation. Runtime loading is local only."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODELS={
 'diarization':{'repository':'mlx-community/Nemotron-3-Diarization','revision':'59ed2dbfc1346dcea9d423c71306a3a2499c568f','files':['config.json','model.safetensors','README.md']},
 'speaker':{'repository':'aufklarer/SpeechBrain-ECAPA-VoxCeleb-20M-MLX','revision':'e749e6e08557f4a3ceb6ce3bf6f0b79efe592a77','files':['config.json','model.safetensors','artifact_manifest.json','validation.json','LICENSE','README.md']}}
SPEAKER_PROFILE='SpeechBrain-logmel400-160-hamming80-mean-v1:mlx-audio-0.6.3:192'
def speaker_revision():return MODELS['speaker']['repository']+'@'+MODELS['speaker']['revision']+':'+SPEAKER_PROFILE
def _sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def _atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as stream:json.dump(data,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    tmp.replace(path)
def _valid(path,spec):
    if not path.is_file() or path.stat().st_size!=spec['size']:return False
    if spec.get('sha256'):return _sha(path)==spec['sha256']
    data=path.read_bytes();return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==spec['git_blob']
def check(root=ROOT):
    root=Path(root);lock=root/'models/model-lock.json'
    if not lock.is_file():return {'ready':False,'reason':'model lock is missing'}
    manifest=json.loads(lock.read_text());errors=[]
    for kind,model in manifest.items():
        if model['revision']!=MODELS[kind]['revision']:errors.append(kind+': wrong revision');continue
        for spec in model['files']:
            if not _valid(root/'models'/kind/spec['path'],spec):errors.append(kind+'/'+spec['path'])
    return {'ready':not errors,'errors':errors,'speaker_revision':speaker_revision(),'models':manifest}
def prepare(root=ROOT):
    root=Path(root);manifest={}
    for kind,model in MODELS.items():
        url='https://huggingface.co/api/models/'+model['repository']+'/tree/'+model['revision']+'?recursive=true&expand=true'
        tree=json.load(urllib.request.urlopen(url,timeout=30));files=[]
        for name in model['files']:
            item=next(x for x in tree if x.get('path')==name)
            files.append({'path':name,'size':item['size'],'sha256':item.get('lfs',{}).get('oid'),'git_blob':item.get('oid')})
        manifest[kind]={**model,'files':files}
    _atomic(root/'models/model-lock.json',manifest)
    def download(args):
        kind,model,spec=args;path=root/'models'/kind/spec['path'];path.parent.mkdir(parents=True,exist_ok=True)
        if _valid(path,spec):return
        tmp=path.with_name(path.name+'.part')
        url='https://huggingface.co/'+model['repository']+'/resolve/'+model['revision']+'/'+spec['path']+'?download=true'
        with urllib.request.urlopen(url,timeout=60) as response,tmp.open('wb') as output:
            while chunk:=response.read(1024*1024):output.write(chunk)
            output.flush();os.fsync(output.fileno())
        if not _valid(tmp,spec):raise RuntimeError('Model verification failed: '+kind+'/'+spec['path'])
        tmp.replace(path)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(download,[(k,m,s) for k,m in manifest.items() for s in m['files']]))
    result=check(root);_atomic(root/'models/readiness.json',result)
    if not result['ready']:raise RuntimeError(result['errors'])
    return result
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=check() if args.check else prepare();print(json.dumps(r,indent=2));raise SystemExit(0 if r['ready'] else 1)
