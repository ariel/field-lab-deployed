import json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from lab_indexer.guards import ROOT
from lab_indexer.pipeline import Pipeline
class FaceStageTests(unittest.TestCase):
 def test_atomic_stage_separate_from_immutable_raw_and_resume(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'projects') as folder:
   root=Path(folder);raw=root/'raw';raw.mkdir();(raw/'frame.jpg').write_bytes(b'original');result={'highlights':[{'seconds':1.,'frame':'frame.jpg'}]}
   pipeline=Pipeline(root/'project',faces=True)
   class Fake:
    calls=0
    def analyze(self,frames,output,input_root=None):
     self.calls+=1;self.source=input_root
     (output/'faces').mkdir();(output/'faces/0.jpg').write_bytes(b'crop')
     return {'observations':[],'counts':{'frames':1}}
   fake=Fake();pipeline.face_models=fake
   try:
    a,profile,reused=pipeline._face_analysis('abc',result,raw);self.assertFalse(reused);self.assertEqual(fake.calls,1)
    b,_,reused=pipeline._face_analysis('abc',result,raw);self.assertTrue(reused);self.assertEqual(fake.calls,1);self.assertEqual(a,b)
    self.assertEqual((raw/'frame.jpg').read_bytes(),b'original');self.assertEqual(list(raw.iterdir()),[raw/'frame.jpg'])
    target=root/'project/_DIT_NOTES/.faces/abc'/profile;(target/'faces/0.jpg').write_bytes(b'corrupt')
    _,_,reused=pipeline._face_analysis('abc',result,raw);self.assertFalse(reused);self.assertEqual(fake.calls,2)
   finally:pipeline.close()
 def test_representative_face_warmup_is_discarded(self):
  from lab_indexer.faces import FaceModels
  models=FaceModels();result=models.prewarm()
  self.assertTrue(result['discarded']);self.assertEqual(result['backend'],'OpenCV DNN CPU')
  self.assertIsNotNone(models.detector);self.assertIsNotNone(models.recognizer)
 def test_auto_face_policy_fails_closed(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'projects') as folder:
   with self.assertRaises(ValueError):Pipeline(Path(folder)/'p',faces=True,face_policy={'auto_assign':True,'threshold':.01})
if __name__=='__main__':unittest.main()
