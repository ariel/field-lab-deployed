#!/usr/bin/env python3
"""Prepare exact OpenAI CLIP weights for the pinned official Apple MLX example.

PyTorch is isolated in .conversion-venv for one-time conversion; runtime is MLX.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,time,urllib.request,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPOSITORY='openai/clip-vit-base-patch32'
SOURCE_REVISION='3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268'
IMPLEMENTATION_REVISION='09b641aaa74f9737f747b62ad8c628405e7e25be'
SOURCE_SHA256='a63082132ba4f97a80bea76823f544493bffa8082296d62d71581a4feff1576f'
SOURCE_BYTES=605247071
PRECISION='float16'
PROFILE=hashlib.sha256((REPOSITORY+SOURCE_REVISION+IMPLEMENTATION_REVISION+PRECISION+':converter-v2:tokenizers-json:normalized-v1').encode()).hexdigest()
CONFIG_LOCK=json.loads('[{"path":"config.json","bytes":4186,"git_blob_sha1":"a2a88b96561196777ca173b15309ea859f4d2ce0"},{"path":"preprocessor_config.json","bytes":316,"git_blob_sha1":"5a12a1eb250987a4eee0e3e7d7338c4b22724be1"},{"path":"tokenizer.json","bytes":2224041,"git_blob_sha1":"564c0ebd5ce29c4ee4864004aee693deadd3128c"},{"path":"tokenizer_config.json","bytes":592,"git_blob_sha1":"4fdaf6842dd5a725b940c92b6b692490ce59d548"},{"path":"special_tokens_map.json","bytes":389,"git_blob_sha1":"9bfb42aa97dcd61e89f279ccaee988bccb4fabae"},{"path":"vocab.json","bytes":862328,"git_blob_sha1":"182766ce89b439768edadda342519f33802f5364"},{"path":"merges.txt","bytes":524657,"git_blob_sha1":"bbfec752c9a675946c6dce106def6f35c882dcc2"}]')
VENDOR_LOCK=json.loads('[{"path":"model.py","url":"https://raw.githubusercontent.com/ml-explore/mlx-examples/09b641aaa74f9737f747b62ad8c628405e7e25be/clip/model.py","bytes":14136,"sha256":"d54420b29ebbb6dbee29d0359ab4de581aa8d190d50b55a5fbd6998ee62c58a7"},{"path":"image_processor.py","url":"https://raw.githubusercontent.com/ml-explore/mlx-examples/09b641aaa74f9737f747b62ad8c628405e7e25be/clip/image_processor.py","bytes":2925,"sha256":"8ed050d13d2d8debde95574af9c8ba873749d73d7283a61c64e93806b1c836d7"},{"path":"LICENSE","url":"https://raw.githubusercontent.com/ml-explore/mlx-examples/09b641aaa74f9737f747b62ad8c628405e7e25be/LICENSE","bytes":1066,"sha256":"ccfab7ccb2ea306f71531c8ca77bb55507606cd90768b1e32b8b52ab5b48cf01"}]')
def _sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def _save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)
def _config_valid(path,spec):
 if not path.is_file() or path.stat().st_size!=spec['bytes']:return False
 data=path.read_bytes();return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==spec['git_blob_sha1']
def _download(url,path,sha=None,size=None):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.is_file() and (size is None or path.stat().st_size==size) and (sha is None or _sha(path)==sha):return
 tmp=path.with_name(path.name+'.part')
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Fieldnotes-MLX-CLIP'}),timeout=90) as source,tmp.open('wb') as dest:shutil.copyfileobj(source,dest,length=1024*1024)
   if size is not None and tmp.stat().st_size!=size:raise ValueError('Downloaded size mismatch')
   if sha and _sha(tmp)!=sha:raise ValueError('Downloaded checksum mismatch')
   tmp.replace(path);return
  except Exception:
   if attempt==2:raise
   time.sleep(2**attempt)
def check(root=ROOT,write=False):
 root=Path(root).resolve();directory=root/'models/mlx-search/clip';manifest=directory/'manifest.json';errors=[];files=[]
 try:data=json.loads(manifest.read_text())
 except (FileNotFoundError,ValueError):data={}
 if data.get('profile')!=PROFILE:errors.append('Missing or incompatible prepared model manifest')
 for spec in CONFIG_LOCK:
  path=directory/spec['path'];valid=_config_valid(path,spec)
  files.append({'path':spec['path'],'ready':valid})
  if not valid:errors.append('Missing/corrupt '+spec['path'])
 for spec in VENDOR_LOCK:
  path=directory/'_vendor'/spec['path'];valid=path.is_file() and path.stat().st_size==spec['bytes'] and _sha(path)==spec['sha256']
  files.append({'path':'_vendor/'+spec['path'],'ready':valid})
  if not valid:errors.append('Missing/corrupt official implementation '+spec['path'])
 weights=directory/'model.safetensors';expected=data.get('weights',{});valid=weights.is_file() and weights.stat().st_size==expected.get('bytes') and _sha(weights)==expected.get('sha256')
 files.append({'path':'model.safetensors','ready':valid})
 if not valid:errors.append('Missing/corrupt MLX weights')
 result={'ready':not errors,'revision':{'clip':PROFILE},'repository':REPOSITORY,'source_revision':SOURCE_REVISION,'implementation':'ml-explore/mlx-examples/clip','implementation_revision':IMPLEMENTATION_REVISION,'precision':PRECISION,'dimension':512,'files':files,'errors':errors}
 if write:_save(root/'models/.runtime/mlx-clip-readiness.json',result)
 return result
def _converter_python(root):
 """Bootstrap the isolated converter only when native weights need conversion."""
 root=Path(root).resolve();environment=root/'.conversion-venv';python=environment/'bin/python'
 requirements=root/'requirements-converter.lock.txt'
 if not requirements.is_file():raise RuntimeError('Missing pinned requirements-converter.lock.txt')
 fingerprint=hashlib.sha256(requirements.read_bytes()).hexdigest();marker=environment/'requirements.sha256'
 if python.is_file() and marker.is_file() and marker.read_text().strip()==fingerprint:return python
 uv=shutil.which('uv')
 if not uv:raise RuntimeError('uv is required to bootstrap the isolated one-time converter')
 if not python.is_file():subprocess.run([uv,'venv',str(environment),'--python',sys.executable],check=True)
 command=[uv,'pip','sync','--python',str(python),str(requirements)]
 cached=subprocess.run(command[:3]+['--offline']+command[3:],capture_output=True,text=True)
 if cached.returncode:subprocess.run(command,check=True)
 marker.write_text(fingerprint+'\n')
 return python

def _convert_cpu(source,target):
 """Executed solely by .conversion-venv; never imported by the MLX runtime."""
 import torch
 import numpy as np
 from safetensors.numpy import save_file
 torch.set_num_threads(1)
 state=torch.load(str(source),map_location='cpu',weights_only=True)
 arrays={name:np.array(tensor.detach().cpu().numpy(),dtype=np.float16,copy=True,order='C') for name,tensor in state.items() if 'position_ids' not in name}
 save_file(arrays,str(target))

def prepare(root=ROOT):
 root=Path(root).resolve();directory=root/'models/mlx-search/clip';directory.mkdir(parents=True,exist_ok=True)
 for spec in CONFIG_LOCK:
  path=directory/spec['path']
  if not _config_valid(path,spec):
   _download('https://huggingface.co/'+REPOSITORY+'/resolve/'+SOURCE_REVISION+'/'+spec['path']+'?download=true',path,size=spec['bytes'])
   if not _config_valid(path,spec):raise ValueError('Pinned config verification failed: '+spec['path'])
 for spec in VENDOR_LOCK:_download(spec['url'],directory/'_vendor'/spec['path'],sha=spec['sha256'],size=spec['bytes'])
 if not check(root)['ready']:
  source=Path.home()/'.cache/huggingface/hub/models--openai--clip-vit-base-patch32/snapshots'/SOURCE_REVISION/'pytorch_model.bin'
  if not source.is_file() or source.stat().st_size!=SOURCE_BYTES or _sha(source)!=SOURCE_SHA256:
   source=directory/'.source/pytorch_model.bin'
   _download('https://huggingface.co/'+REPOSITORY+'/resolve/'+SOURCE_REVISION+'/pytorch_model.bin?download=true',source,sha=SOURCE_SHA256,size=SOURCE_BYTES)
  converter=_converter_python(root)
  print('Converting verified OpenAI checkpoint in isolated .conversion-venv',flush=True)
  target=directory/'model.safetensors';partial=directory/'model.safetensors.part'
  subprocess.run([str(converter),str(Path(__file__).resolve()),'--convert',str(source),str(partial)],check=True)
  partial.replace(target)
  _save(directory/'manifest.json',{'profile':PROFILE,'repository':REPOSITORY,'source_revision':SOURCE_REVISION,'source_sha256':SOURCE_SHA256,'implementation_revision':IMPLEMENTATION_REVISION,'precision':PRECISION,'weights':{'path':'model.safetensors','bytes':target.stat().st_size,'sha256':_sha(target)},'converter':'torch.load(weights_only=True), tensor float16, safetensors.numpy.save_file; official MLX loader handles layout'})
 result=check(root,write=True)
 if not result['ready']:raise RuntimeError('; '.join(result['errors']))
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--check',action='store_true');p.add_argument('--convert',nargs=2,metavar=('SOURCE','OUTPUT'),help=argparse.SUPPRESS)
 a=p.parse_args()
 if a.convert:_convert_cpu(Path(a.convert[0]),Path(a.convert[1]));return 0
 result=check(a.root,write=True) if a.check else prepare(a.root);print(json.dumps(result,indent=2));return 0 if result['ready'] else 2
if __name__=='__main__':raise SystemExit(main())
