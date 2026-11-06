import sys,unittest,tempfile,json,math,hashlib
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
ROOT=Path('/Volumes/ThunderBlade X8/AI Indexer Lab/release');sys.path.insert(0,str(ROOT))
from ditnotes import library
from ditnotes.models import speaker_revision
from ditnotes.face_models import embedding_revision
from ditnotes.project_store import ProjectStore
from ditnotes.enrichment import publish_index
from ditnotes.catalog_index import read_snapshot
class FakeEngine:
 def __init__(self):self.calls=0;self.progress_callback=None
 def analyze(self,source,output):
  self.calls+=1;output=Path(output);(output/'frames').mkdir();(output/'faces').mkdir();(output/'tracks').mkdir()
  from PIL import Image
  Image.new('RGB',(64,64)).save(output/'frames/0.jpg');Image.new('RGB',(112,112)).save(output/'faces/0.jpg')
  for n in ['json','txt','srt']:(output/f'tracks/0.{n}').write_text('{}' if n=='json' else 'Hello world')
  if self.progress_callback:self.progress_callback('asr');self.progress_callback('vlm')
  result={'status':'complete','duration':10.,'probe':{'streams':[{'codec_type':'video','width':64,'height':64}]},'highlights':[{'seconds':1.,'label':'Field','frame':'frames/0.jpg','audio_context':[{'text':'Hello world'}]}],
   'tracks':[{'stream_index':0,'sentences':[{'start':0.,'end':4.,'text':'Hello world'}],'json':'tracks/0.json','text_file':'tracks/0.txt','srt':'tracks/0.srt','diarization':{'speaker_model_revision':speaker_revision(),'turns':[{'start':0.,'end':4.,'local_speaker':'0','overlap':False}],
    'local_speakers':[{'local_speaker':'0','embedding':[1.]+[0.]*191,'model_revision':speaker_revision(),'quality':1.,'quality_components':{},'enrollment_windows':[{'start':0.,'end':4.}]}],'token_speakers':[]}}],
   'faces':{'observations':[{'seconds':1.,'embedding':[1.]+[0.]*127,'model_revision':embedding_revision(),'quality':1.,'bbox':[.1,.1,.8,.8],'frame':'frames/0.jpg','crop':'faces/0.jpg','detection_id':'0','quality_components':{}}]},'timing':{'total_seconds':.01}}
  (output/'result.json').write_text(json.dumps(result));return result
 def close(self):pass
class Backend:
 def __init__(self):self.executor=ThreadPoolExecutor(1);self.calls=0
 def readiness(self):return {'ready':True,'revision':{'text':'text-fixture','clip':'clip-fixture','reranker':'rerank-fixture'}}
 def _infer(self,action,values,query=''):
  self.calls+=1;dim=384 if action=='embed_text' else 512
  return {'vectors':[[1/math.sqrt(dim)]*dim for _ in values]}
 def close(self):self.executor.shutdown()
class UnifiedTests(unittest.TestCase):
 def test_process_registry_search_edit_restart_duplicate(self):
  with tempfile.TemporaryDirectory(prefix='unified-',dir=ROOT.parent/'release-validation') as folder:
   project=Path(folder);source=project/'A.mp4';source.write_bytes(b'first');duplicate=project/'Acopy.mp4';duplicate.write_bytes(b'first');engine=FakeEngine();events=[]
   a=library.process(project,project,engine=engine,progress_event=events.append)
   self.assertEqual(a['counts']['processed'],1);self.assertEqual(a['counts']['reused'],1);self.assertEqual(engine.calls,1)
   self.assertTrue(any(e['stage']=='asr' for e in events));self.assertEqual(events[-1]['completed'],2)
   identity=json.loads((project/'_DIT_NOTES/project.json').read_text())
   with ProjectStore(project/'_DIT_NOTES/project.sqlite3',project_id=identity['id']) as store:
    self.assertEqual(len(store.people()),1);self.assertEqual(len(store.faces()),1);person=store.people()[0]['id'];face=store.faces()[0]['id'];store.name_person(person,'Ariel');store.name_face(face,'Face A')
    self.assertIsNone(store.faces()[0]['voice_link']);store.link_face_voice(face,person,'Operator test')
    store.add_annotation(hashlib.sha256(b'first').hexdigest(),'Prairie interview',metadata={'tags':['pickup']})
   other=project/'B.mp4';other.write_bytes(b'second');library.process(other,project,engine=engine)
   backend=Backend()
   try:
    published=publish_index(project,backend);self.assertTrue(published['ready']);snapshot=read_snapshot(project);self.assertIsNotNone(snapshot)
    documents=snapshot['catalog']['search_projection']['documents'];self.assertTrue(any('pickup' in d['text'] for d in documents));self.assertTrue(any('Ariel' in d['personNames'] for d in documents))
    with ProjectStore(project/'_DIT_NOTES/project.sqlite3') as store:
     links=store.links(hashlib.sha256(b'second').hexdigest());self.assertTrue(links);self.assertFalse(store.annotations(hashlib.sha256(b'second').hexdigest()));store.accept_link(links[0]['id'])
    publish_index(project,backend)
    b=library.process(project,project,engine=engine);self.assertEqual(b['counts']['processed'],0);self.assertEqual(engine.calls,2)
   finally:backend.close()
 def test_sealed_analysis_registry_interruption_repaired_on_startup(self):
  with tempfile.TemporaryDirectory(dir=ROOT.parent/'release-validation') as folder:
   project=Path(folder);source=project/'A.mp4';source.write_bytes(b'recover');engine=FakeEngine()
   with patch('ditnotes.enrichment.register_result',side_effect=RuntimeError('interrupt after seal')):
    a=library.process(source,project,engine=engine);self.assertEqual(a['counts']['failed'],1)
   resumed=library.reconcile(project,input_paths=[source]);self.assertFalse(resumed['pending']);self.assertEqual(engine.calls,1)
   with ProjectStore(project/'_DIT_NOTES/project.sqlite3') as store:self.assertEqual(len(store.people()),1);self.assertEqual(len(store.faces()),1)
 def test_merge_contradictions_rejected(self):
  with tempfile.TemporaryDirectory(dir=ROOT.parent/'release-validation') as folder:
   with ProjectStore(Path(folder)/'store.sqlite3') as store:
    a=store.provisional_speaker('clip','a',0,3,overlap_group='stream0')['person_id'];b=store.provisional_speaker('clip','b',1,4,overlap_group='stream0')['person_id']
    with self.assertRaises(ValueError):store.merge_people(a,b,'test')
    one=store.assign_face('clip',1,[1.,0.],'face-model',1,bbox=[0,0,.3,.3],detection_id='a')['face_id'];two=store.assign_face('clip',1,[0.,1.],'face-model',1,bbox=[.5,.5,1,1],detection_id='b')['face_id']
    with self.assertRaises(ValueError):store.merge_faces(one,two,'test')
if __name__=='__main__':unittest.main()
