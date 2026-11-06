from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import cv2
from lab_indexer.faces import FaceModels
cv2.setNumThreads(1)
folder=ROOT/'fixtures/faces';imgs=[cv2.imread(str(folder/(p+'.jpg'))) for p in ['person-a','person-b']]
imgs=[cv2.resize(i,(400,500)) for i in imgs];montage=cv2.hconcat(imgs);cv2.imwrite(str(folder/'two-portraits.jpg'),montage)
frames=[{'seconds':i,'frame':'two-portraits.jpg'} for i in range(12)]
model=FaceModels();runs=[]
for i in range(3):
 out=ROOT/'benchmarks/faces'/f'bound-{i}';out.mkdir(exist_ok=True);runs.append(model.analyze(frames,out,input_root=folder))
payload={'runs':runs,'scope':'Twelve duplicate two-face frames exercise exact-crop cache and per-frame bounds. Not worst-case unique24-crop runtime.'};(ROOT/'benchmarks/faces-bound.json').write_text(json.dumps(payload,indent=2));print(json.dumps([{'counts':r['counts'],'timing':r['timing']} for r in runs]))
