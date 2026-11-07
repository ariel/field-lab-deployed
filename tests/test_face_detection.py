"""Bounded small-face retry and source-coordinate/quality contracts; no weights."""
import tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from ditnotes.faces import FaceModels,_source_rows,DETECTION_POLICY

def row(x=100,y=50,w=60,h=70):
 return np.array([x,y,w,h,x+15,y+20,x+45,y+20,x+30,y+35,x+20,y+50,x+40,y+50,.95],dtype=np.float32)
class Detector:
 def __init__(self,results):self.results=list(results);self.sizes=[];self.images=[]
 def setInputSize(self,size):self.sizes.append(size)
 def detect(self,image):
  self.images.append(image.shape)
  result=self.results.pop(0)
  if isinstance(result,Exception):raise result
  return None,result
class Recognizer:
 def __init__(self):self.rows=[];self.forwards=0
 def alignCrop(self,image,r):self.rows.append(r.copy());return np.zeros((112,112,3),dtype=np.uint8)
 def feature(self,image):self.forwards+=1;return np.array([[1.,0.,0.]],dtype=np.float32)
class Detection(unittest.TestCase):
 def fake_cv(self,image):
  def save(path,crop):Path(path).write_bytes(b'generated crop');return True
  return types.SimpleNamespace(resize=lambda im,size:np.zeros((size[1],size[0],3),dtype=np.uint8),imread=lambda path:image.copy(),imwrite=save,Laplacian=lambda im,dtype:np.array([0.,20.]),cvtColor=lambda im,kind:im[:,:,0],COLOR_BGR2GRAY=1,CV_64F=1)
 def model(self,results):
  model=FaceModels();model.detector=Detector(results);model.recognizer=Recognizer();return model
 def test_box_and_all_landmarks_use_actual_rounded_xy_scale(self):
  original=row();mapped,bad=_source_rows([original],(1001,1901,3),(337,640,3));self.assertEqual(bad,0)
  np.testing.assert_allclose(mapped[0][:14:2],original[:14:2]*1901/640)
  np.testing.assert_allclose(mapped[0][1:14:2],original[1:14:2]*1001/337)
  self.assertEqual(mapped[0][-1],original[-1]);np.testing.assert_array_equal(original,row())
 def test_base_detection_skips_retry_and_does_not_duplicate_rows(self):
  image=np.zeros((360,640,3),dtype=np.uint8);model=self.model([[row()]])
  with patch.dict('sys.modules',cv2=self.fake_cv(image)):rows,stats=model._detect_faces(image)
  self.assertEqual(len(rows),1);self.assertEqual(stats['detector_passes'],1);self.assertEqual(stats['fallback_frames'],0);self.assertEqual(len(model.detector.sizes),1)
 def test_empty_base_gets_only_one_retry_capped_at_1280(self):
  image=np.zeros((2160,3840,3),dtype=np.uint8);model=self.model([None,None])
  with patch.dict('sys.modules',cv2=self.fake_cv(image)):rows,stats=model._detect_faces(image)
  self.assertEqual(rows,[]);self.assertEqual(model.detector.sizes,[(640,360),(1280,720)]);self.assertEqual(stats['detector_passes'],2)
 def test_small_images_upscale_at_most_two_times(self):
  image=np.zeros((120,200,3),dtype=np.uint8);model=self.model([None,None])
  with patch.dict('sys.modules',cv2=self.fake_cv(image)):model._detect_faces(image)
  self.assertEqual(model.detector.sizes,[(200,120),(400,240)])
 def test_frame_bound_also_bounds_retry_work(self):
  image=np.zeros((360,640,3),dtype=np.uint8);model=self.model([None,None]);model.max_frames=1
  with tempfile.TemporaryDirectory() as tmp,patch.dict('sys.modules',cv2=self.fake_cv(image)):
   result=model.analyze([{'seconds':1.,'frame':'one.jpg'},{'seconds':2.,'frame':'two.jpg'}],tmp)
  self.assertEqual(len(model.detector.sizes),2);self.assertEqual(result['counts']['frames'],1)
  self.assertEqual(result['counts']['omitted_frames'],1);self.assertEqual(result['counts']['fallback_frames'],1)
 def test_invalid_boxes_landmarks_and_scores_are_rejected(self):
  bad=[row(),row(),row(),row(),np.zeros(14,dtype=np.float32)]
  bad[0][4]=float('nan');bad[1][3]=-1;bad[2][-1]=2;bad[3][9]=float('inf')
  valid,invalid=_source_rows(bad,(360,640,3),(360,640,3));self.assertEqual(valid,[]);self.assertEqual(invalid,5)
 def test_detector_error_is_not_hidden_as_a_miss(self):
  image=np.zeros((360,640,3),dtype=np.uint8);model=self.model([RuntimeError('detector failed')])
  with patch.dict('sys.modules',cv2=self.fake_cv(image)),self.assertRaisesRegex(RuntimeError,'detector failed'):model._detect_faces(image)
  self.assertEqual(len(model.detector.sizes),1)
 def test_retry_crop_keeps_source_quality_guard_and_is_not_enrolled(self):
  image=np.zeros((540,960,3),dtype=np.uint8);model=self.model([None,[row(w=58.66667,h=72)]])
  with tempfile.TemporaryDirectory() as tmp,patch.dict('sys.modules',cv2=self.fake_cv(image)):
   result=model.analyze([{'seconds':4.,'frame':'frame.jpg'}],tmp)
   self.assertTrue((Path(tmp)/result['observations'][0]['crop']).is_file())
  observation=result['observations'][0];self.assertAlmostEqual(observation['quality_components']['face_pixels'],44.,places=4)
  self.assertEqual(observation['reason'],'low_quality_crop');self.assertIsNone(observation['embedding']);self.assertEqual(model.recognizer.forwards,0)
  self.assertEqual(observation['detection_id'],'0-0');self.assertEqual(result['detection_policy'],DETECTION_POLICY);self.assertEqual(result['counts']['fallback_detected'],1)
 def test_existing_eligible_detection_keeps_id_and_embedding_cache(self):
  image=np.zeros((360,640,3),dtype=np.uint8);model=self.model([[row()],[row()]])
  with tempfile.TemporaryDirectory() as tmp,patch.dict('sys.modules',cv2=self.fake_cv(image)):
   result=model.analyze([{'seconds':1.,'frame':'one.jpg'},{'seconds':2.,'frame':'two.jpg'}],tmp)
  self.assertEqual([o['detection_id'] for o in result['observations']],['0-0','1-0']);self.assertEqual(model.recognizer.forwards,1);self.assertEqual(result['counts']['cache_hits'],1)
  self.assertEqual(result['counts']['fallback_frames'],0);self.assertTrue(all(o['embedding'] for o in result['observations']))
if __name__=='__main__':unittest.main()
