"""Pinned official OpenCV Zoo face assets; no runtime network access."""
from pathlib import Path
import hashlib,json,urllib.request,os,uuid
from .guards import ROOT
REVISION='48b10fa505aeb51fbd127fc60a5c660040e823b7'
ASSETS={
 'yunet.onnx':('face_detection_yunet/face_detection_yunet_2023mar.onnx','MIT'),
 'sface.onnx':('face_recognition_sface/face_recognition_sface_2021dec.onnx','Apache-2.0'),
 'YUNET-LICENSE':('face_detection_yunet/LICENSE','MIT'),
 'SFACE-LICENSE':('face_recognition_sface/LICENSE','Apache-2.0'),
 'YUNET-README.md':('face_detection_yunet/README.md','MIT'),
 'SFACE-README.md':('face_recognition_sface/README.md','Apache-2.0')}
def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def prepare():
 folder=ROOT/'models/faces';folder.mkdir(parents=True,exist_ok=True);records=[]
 for name,(relative,license) in ASSETS.items():
  source=f'https://raw.githubusercontent.com/opencv/opencv_zoo/{REVISION}/models/{relative}'
  metadata=urllib.request.urlopen(source).read();expected=None
  if name.endswith('.onnx'):
   text=metadata.decode();expected=next(s.split('sha256:')[1] for s in text.splitlines() if s.startswith('oid sha256:'))
   source=f'https://media.githubusercontent.com/media/opencv/opencv_zoo/{REVISION}/models/{relative}'
  target=folder/name
  if not target.exists() or (expected and digest(target)!=expected):
   data=urllib.request.urlopen(source).read() if expected else metadata
   part=target.with_name(name+'.'+uuid.uuid4().hex+'.part');part.write_bytes(data)
   if expected and digest(part)!=expected:part.unlink();raise ValueError('Face model digest mismatch')
   with part.open('rb') as f:os.fsync(f.fileno())
   part.replace(target)
  records.append({'file':name,'source':source,'sha256':digest(target),'bytes':target.stat().st_size,'license':license})
 from .atomic import atomic_json
 atomic_json(folder/'manifest.json',{'revision':REVISION,'files':records})
 return check()
def check():
 folder=ROOT/'models/faces';errors=[]
 try:
  manifest=json.loads((folder/'manifest.json').read_text())
  if manifest['revision']!=REVISION:errors.append('Wrong revision')
  for row in manifest['files']:
   if digest(folder/row['file'])!=row['sha256']:errors.append(row['file'])
 except (OSError,KeyError,ValueError) as exc:errors.append(str(exc))
 return {'ready':not errors,'errors':errors,'revision':REVISION,'backend':'OpenCV DNN CPU'}
def embedding_revision():
 return f'opencv-zoo@{REVISION}:SFace-2021dec:opencv-alignCrop5-BGR112:128:l2-v1'
if __name__=='__main__':print(json.dumps(prepare(),indent=2))
