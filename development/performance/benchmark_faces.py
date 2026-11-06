"""Explicit CPU-only face regression and bounded-stage timing; no MLX imports."""
from pathlib import Path
import sys,json,time,hashlib,urllib.request
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import cv2,numpy as np
from lab_indexer.faces import FaceModels
cv2.setNumThreads(1)
fixture=ROOT/'fixtures/faces';fixture.mkdir(parents=True,exist_ok=True)
sources=[('person-a','https://raw.githubusercontent.com/scikit-image/scikit-image/v0.20.0/skimage/data/astronaut.png','NASA public-domain image; scikit-image astronaut documentation'),('person-b','https://raw.githubusercontent.com/matplotlib/matplotlib/v3.10.0/lib/matplotlib/mpl-data/sample_data/grace_hopper.jpg','US Navy public-domain image; matplotlib sample data')]
frames=[];manifest=[]
for ident,url,license_note in sources:
 path=fixture/(ident+'.jpg')
 if not path.exists():
  raw=urllib.request.urlopen(url,timeout=30).read();im=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
  if im is None:raise ValueError(url)
  cv2.imwrite(str(path),im)
 im=cv2.imread(str(path));h,w=im.shape[:2]
 manifest.append({'identity':ident,'source':url,'license_note':license_note,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 for suffix,img in [('original',im),('darker',cv2.convertScaleAbs(im,alpha=.78,beta=5)),('resized',cv2.resize(im,(round(w*.82),round(h*.82))))]:
  name=f'{ident}-{suffix}.jpg';cv2.imwrite(str(fixture/name),img);frames.append({'seconds':len(frames),'frame':name,'identity':ident})
(fixture/'manifest.json').write_text(json.dumps({'sources':manifest,'limitation':'Same-source transformations only; not independent-shot or demographic accuracy calibration.'},indent=2))
out=ROOT/'benchmarks/faces';out.mkdir(exist_ok=True)
model=FaceModels();results=[]
for i in range(3):
 dest=out/f'portraits-{i}';dest.mkdir(exist_ok=True);r=model.analyze(frames,dest,input_root=fixture);results.append(r)
obs=results[-1]['observations'];pairs=[]
for i,a in enumerate(obs):
 for b in obs[i+1:]:
  if a['embedding'] is not None and b['embedding'] is not None:pairs.append({'same':a['frame'].split('-')[1]==b['frame'].split('-')[1],'cosine':float(np.dot(a['embedding'],b['embedding']))})
base=json.loads((ROOT/'benchmarks/full-pipeline.json').read_text());run=base['runs'][0]
stage=next((Path(base['project'])/'_DIT_NOTES/.objects'/run['content_id']).glob('*'))
trailer=[]
for i in range(3):
 dest=out/f'trailer-{i}';dest.mkdir(exist_ok=True);trailer.append(model.analyze(run['highlights'],dest,input_root=stage))
payload={'portrait_runs':results,'pairs':pairs,'same_min':min(p['cosine'] for p in pairs if p['same']),'different_max':max(p['cosine'] for p in pairs if not p['same']),'trailer_runs':trailer,'limitations':['CPU only with OpenCV DNN CPU explicitly selected; one thread. Root production workload may overlap so these are indicative stage costs.','Portrait transforms test stability and different-identity separation only; no production matching threshold calibrated.','Only existing selected stills inspected; faces between samples or rejected by quality/bounds are omitted.']}
(ROOT/'benchmarks/faces-cpu.json').write_text(json.dumps(payload,indent=2));print(json.dumps({'same_min':payload['same_min'],'different_max':payload['different_max'],'portrait_seconds':[r['timing'] for r in results],'trailer':[{k:r[k] for k in ['counts','timing']} for r in trailer]}))
