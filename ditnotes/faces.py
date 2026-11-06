"""Bounded face observations from already-selected stills; official CPU baseline.

Detection means a face-like region, not verified identity. No face attributes or
voice association are inferred. No network calls or image corpus retrieval.
"""
from pathlib import Path
import hashlib,time
import numpy as np
from .guards import ROOT
from .face_models import check,embedding_revision

class FaceModels:
 def __init__(self,*,max_frames=12,max_per_frame=2,max_embeddings=24,min_face_pixels=48):
  self.max_frames=max_frames;self.max_per_frame=max_per_frame;self.max_embeddings=max_embeddings;self.min_face_pixels=min_face_pixels
  self.detector=None;self.recognizer=None
 def load(self):
  if self.detector is not None:return
  if not check()['ready']:raise RuntimeError('Run face prepare-offline before face analysis')
  import cv2
  cv2.setNumThreads(1)
  folder=ROOT/'models/faces'
  self.detector=cv2.FaceDetectorYN.create(str(folder/'yunet.onnx'),'',(640,640),.9,.3,5000,cv2.dnn.DNN_BACKEND_OPENCV,cv2.dnn.DNN_TARGET_CPU)
  self.recognizer=cv2.FaceRecognizerSF.create(str(folder/'sface.onnx'),'',cv2.dnn.DNN_BACKEND_OPENCV,cv2.dnn.DNN_TARGET_CPU)
 def prewarm(self):
  """Discarded CPU detector+recognizer forwards; no crops or identities."""
  started=time.perf_counter();self.load()
  self.detector.setInputSize((640,360));self.detector.detect(np.full((360,640,3),128,dtype=np.uint8))
  vector=self.recognizer.feature(np.full((112,112,3),128,dtype=np.uint8))
  if not np.isfinite(vector).all():raise ValueError('Invalid discarded face warmup')
  return {'seconds':time.perf_counter()-started,'discarded':True,'backend':'OpenCV DNN CPU'}
 def analyze(self,frames,output,*,input_root=None):
  """frames: {seconds,frame:path-relative-to-output}; saves aligned evidence crops."""
  import cv2
  started=time.perf_counter();self.load();load=time.perf_counter()-started
  output=Path(output);input_root=Path(input_root or output).resolve();folder=output/'faces';folder.mkdir(exist_ok=True)
  observations=[];embedding_cache={};counts={'input_frames':len(frames),'omitted_frames':max(0,len(frames)-self.max_frames),'frames':0,'detected':0,'cropped':0,'embedded':0,'cache_hits':0,'omitted_by_bound':0,'invalid_boxes':0}
  for frame in frames[:self.max_frames]:
   path=(input_root/frame['frame']).resolve()
   if not path.is_relative_to(input_root):raise ValueError('Face frame outside output')
   image=cv2.imread(str(path))
   if image is None:raise ValueError('Unreadable face input still')
   counts['frames']+=1;h,w=image.shape[:2];scale=min(1.,640/max(h,w))
   small=cv2.resize(image,(max(32,round(w*scale)),max(32,round(h*scale))))
   self.detector.setInputSize((small.shape[1],small.shape[0]));_,rows=self.detector.detect(small)
   rows=[] if rows is None else sorted(rows,key=lambda x:float(x[2]*x[3]*x[-1]),reverse=True)
   counts['detected']+=len(rows);counts['omitted_by_bound']+=max(0,len(rows)-self.max_per_frame)
   for number,raw in enumerate(rows[:self.max_per_frame]):
    row=np.array(raw,dtype=np.float32);row[:14]/=scale
    x,y,bw,bh=map(float,row[:4]);bbox=np.clip([x/w,y/h,(x+bw)/w,(y+bh)/h],0.,1.).tolist()
    if bbox[0]>=bbox[2] or bbox[1]>=bbox[3]:counts['invalid_boxes']+=1;continue
    detid=f'{counts["frames"]-1}-{number}';crop_ref=f'faces/{detid}.jpg'
    aligned=self.recognizer.alignCrop(image,row)
    if not cv2.imwrite(str(output/crop_ref),aligned):raise OSError('Failed to save face crop')
    counts['cropped']+=1
    sharpness=float(cv2.Laplacian(cv2.cvtColor(aligned,cv2.COLOR_BGR2GRAY),cv2.CV_64F).var())
    eye_distance=float(np.linalg.norm(row[4:6]-row[6:8]));size=min(bw,bh)
    components={'detector_confidence':float(row[-1]),'face_pixels':size,'eye_distance_pixels':eye_distance,'aligned_laplacian_variance':sharpness,'type':'signal_proxy_not_probability'}
    eligible=size>=self.min_face_pixels and eye_distance>=12 and sharpness>=20
    vector=None;reason='low_quality_crop'
    if eligible and counts['embedded']<self.max_embeddings:
     key=hashlib.sha256(aligned.tobytes()).hexdigest()
     if key in embedding_cache:vector=embedding_cache[key];counts['cache_hits']+=1
     else:
      value=np.asarray(self.recognizer.feature(aligned),dtype=np.float32).reshape(-1);norm=float(np.linalg.norm(value))
      if not np.isfinite(value).all() or norm<=1e-8:raise ValueError('Invalid face vector')
      vector=(value/norm).tolist();embedding_cache[key]=vector;counts['embedded']+=1
     reason='eligible'
    elif eligible:reason='embedding_bound';counts['omitted_by_bound']+=1
    observations.append({'seconds':frame['seconds'],'frame':frame['frame'],'crop':crop_ref,'bbox':bbox,'detection_id':detid,'embedding':vector,'model_revision':embedding_revision(),'quality':float(row[-1]) if vector else 0.,'quality_components':components,'reason':reason})
  return {'schema_version':1,'identity_basis':'face','model_revision':embedding_revision(),'backend':'OpenCV DNN CPU','observations':observations,'counts':counts,'timing':{'model_load_seconds':load,'total_seconds':time.perf_counter()-started},'coverage':'Selected stills only; faces between sampled frames may be missed.'}
