import http.client,importlib,sys,tempfile,json,threading,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ditnotes.project_store import ProjectStore
from ditnotes.search_projection import project_documents
from ditnotes.server import create_server
class Backend:
 def __init__(self,*args,**kw):pass
 def close(self):pass
 def readiness(self):return {'ready':False}
class API(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.project=Path(self.temp.name);notes=self.project/'_DIT_NOTES';notes.mkdir()
  cat={'project':{'id':'fixture','name':'Fixture'},'assets':[{'id':'clip','content_id':'sha','name':'clip.mp4','relative_path':'clip.mp4','highlights':[{'seconds':1,'note':'Forest portrait','image_url':'/notes/f.jpg'}],'transcript':[{'start':0,'end':3,'text':'Hello'}]}]};(notes/'catalog.json').write_text(json.dumps(cat))
  with ProjectStore(notes/'project.sqlite3',project_id='fixture') as s:
   self.person=s.provisional_speaker('sha','speaker0',0,3)['person_id'];self.face=s.assign_face('sha',1,None,'testface',.5,bbox=[.1,.1,.5,.5],frame_ref='/notes/f.jpg')['face_id']
  with patch('ditnotes.server.SearchBackend',Backend),patch('ditnotes.metadata_api.MetadataAPI._loop',return_value=None):self.server=create_server(self.project,0,ROOT)
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
 def request(self,path,value=None,origin=None):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port);h={}
  if value is not None:h['Content-Type']='application/json'
  if origin:h['Origin']=origin
  c.request('POST' if value is not None else 'GET',path,json.dumps(value) if value is not None else None,h);r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
 def test_unified_names_notes_projection_and_explicit_link(self):
  for path,value in [('/api/name',{'person_id':self.person,'name':'Xi'}),('/api/face/name',{'face_id':self.face,'name':'Portrait'}),('/api/annotation',{'content_id':'sha','text':'Evening pickup','metadata':{'tags':['north field']},'start':1,'end':2})]:self.assertEqual(self.request(path,value)[0],200)
  state=json.loads(self.request('/api/annotations-state')[1]);self.assertIsNone(state['faces'][0]['voice_link']);self.assertNotIn('embedding',state['observations'][0]);self.assertNotIn('embedding',state['face_observations'][0]);catalog=json.loads(self.request('/api/catalog')[1]);self.assertNotIn('search_projection',catalog);self.assertIn('north field',state['annotations'][0]['metadata']['tags'])
  self.assertEqual(self.request('/api/face/link',{'face_id':self.face,'person_id':self.person})[0],200)
  with ProjectStore(self.project/'_DIT_NOTES/project.sqlite3',project_id='fixture') as store:catalog['search_projection']=project_documents(catalog,store)
  (self.project/'_DIT_NOTES/catalog.json').write_text(json.dumps(catalog))
  catalog=json.loads(self.request('/api/catalog')[1]);self.assertEqual(next(d for d in catalog['search_projection']['documents'] if d['kind']=='visual')['personNames'],['Xi']);self.assertEqual(self.request('/api/face/unlink',{'face_id':self.face})[0],200)
 def test_named_identity_merge_cross_clip_projection(self):
  with ProjectStore(self.project/'_DIT_NOTES/project.sqlite3',project_id='fixture') as s:
   other=s.provisional_speaker('otherclip','speaker0',0,3)['person_id'];s.name_person(other,'Ariel')
   face2=s.assign_face('otherclip',2,None,'testface',.5,bbox=[.1,.1,.5,.5])['face_id'];s.name_face(face2,'Ariel portrait')
  self.assertEqual(self.request('/api/people/merge',{'source_id':self.person,'target_id':other})[0],200)
  self.assertEqual(self.request('/api/face/merge',{'source_id':self.face,'target_id':face2})[0],200)
  with ProjectStore(self.project/'_DIT_NOTES/project.sqlite3',project_id='fixture') as s:
   cat=json.loads((self.project/'_DIT_NOTES/catalog.json').read_text());docs=project_documents(cat,s)['documents'];self.assertEqual(next(d for d in docs if d['kind']=='speech')['personNames'],['Ariel']);self.assertEqual(next(d for d in docs if d['kind']=='visual')['faceNames'],['Ariel portrait'])
 def test_suggestion_requires_accept_and_preserves_source(self):
  with ProjectStore(self.project/'_DIT_NOTES/project.sqlite3',project_id='fixture') as store:
   source=store.add_annotation('oldsha','Operator location note',metadata={'tags':['north field']})
   links=store.suggest_links('sha',[1,0],{'oldsha':{'vector':[1,0],'model_revision':'clip-test'}},'clip-test')
   link=links[0]['id']
  before=json.loads(self.request('/api/annotations-state')[1]);self.assertFalse(any(a['content_id']=='sha' for a in before['annotations']));self.assertEqual(self.request('/api/link/accept',{'link_id':link})[0],200)
  after=json.loads(self.request('/api/annotations-state')[1]);self.assertTrue(any(a['id']==source and a['source']=='operator' for a in after['annotations']));accepted=next(a for a in after['annotations'] if a['content_id']=='sha');self.assertNotEqual(accepted['source'],'operator');self.assertTrue(accepted['source_id'])
 def test_same_origin_and_unknown_clip(self):
  self.assertEqual(self.request('/api/name',{'person_id':self.person,'name':'Other'},origin='https://example.com')[0],403);self.assertEqual(self.request('/api/annotation',{'content_id':'other','text':'No'})[0],400)
if __name__=='__main__':unittest.main()
