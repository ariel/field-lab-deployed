from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import cv2
from lab_indexer.faces import FaceModels
cv2.setNumThreads(1);folder=ROOT/'fixtures/faces';im=cv2.imread(str(folder/'two-portraits.jpg'));frames=[]
for i in range(12):
 name=f'two-portraits-var-{i}.jpg';cv2.imwrite(str(folder/name),cv2.convertScaleAbs(im,alpha=.8+i*.016,beta=i));frames.append({'seconds':i,'frame':name})
model=FaceModels();runs=[]
for i in range(3):
 out=ROOT/'benchmarks/faces'/f'unique-{i}';out.mkdir(exist_ok=True);runs.append(model.analyze(frames,out,input_root=folder))
(ROOT/'benchmarks/faces-unique.json').write_text(json.dumps({'runs':runs,'scope':'24 distinct eligible crops,12frames,brightness changes prevent exact-crop cache.'},indent=2));print(json.dumps([{'counts':r['counts'],'timing':r['timing']} for r in runs]))
