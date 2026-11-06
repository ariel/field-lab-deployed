import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lab_indexer.project_store import ProjectStore
from lab_indexer.search_projection import project_documents
class Faces(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=ProjectStore(Path(self.tmp.name)/'p.sqlite3')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def face(self,content='a',embedding=(1,0),**kw):return self.store.assign_face(content,1,embedding,'sface128:test',.9,bbox=[.1,.1,.5,.5],frame_ref='/notes/frame.jpg',**kw)
 def test_upgrade_names_persist(self):
  first=self.face(embedding=None);self.store.name_face(first['face_id'],'Portrait');second=self.face();self.assertEqual(first['face_id'],second['face_id']);self.assertTrue(second['enrolled']);self.assertEqual(self.store.faces()[0]['name'],'Portrait')
 def test_same_frame_excludes_and_unknown_not_forced(self):
  a=self.face();b=self.face(detection_id='second',auto_assign=True);self.assertNotEqual(a['face_id'],b['face_id']);c=self.face('c',embedding=(0,1),auto_assign=True);self.assertNotIn(c['face_id'],[a['face_id'],b['face_id']])
 def test_cross_clip_policy_and_revision(self):
  a=self.face();b=self.face('b',auto_assign=True);self.assertEqual(a['face_id'],b['face_id']);self.assertRaises(ValueError,self.face,'c',(1,0,0))
 def test_no_narration_to_face_link(self):
  f=self.face();speaker=self.store.provisional_speaker('a','s',0,3)['person_id'];self.store.name_person(speaker,'Narrator');self.store.name_face(f['face_id'],'Portrait')
  cat={'assets':[{'id':'a','content_id':'a','name':'a.mp4','highlights':[{'seconds':1,'note':'Portrait outdoors','image_url':'/notes/frame.jpg'}],'transcript':[{'start':0,'end':3,'text':'Hello'}]}]}
  docs=project_documents(cat,self.store)['documents'];visual=next(d for d in docs if d['kind']=='visual');speech=next(d for d in docs if d['kind']=='speech');self.assertFalse(visual['personIds']);self.assertEqual(speech['personIds'],[speaker]);self.assertFalse(speech['faceIds'])
  self.store.link_face_voice(f['face_id'],speaker,'Operator verified');docs=project_documents(cat,self.store)['documents'];self.assertEqual(next(d for d in docs if d['kind']=='visual')['personIds'],[speaker]);self.store.unlink_face_voice(f['face_id'],'Correction');self.assertIsNone(self.store.faces()[0]['voice_link'])
if __name__=='__main__':unittest.main()
