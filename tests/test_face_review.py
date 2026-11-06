import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ditnotes.project_store import ProjectStore
from ditnotes.identity_grouping import regroup
from ditnotes.av_links import proposals

class Review(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'project.sqlite3';self.s=ProjectStore(self.path,'fixture')
 def tearDown(self):self.s.close();self.tmp.cleanup()
 def face(self,clip,vector):return self.s.assign_face(clip,2,vector,'model',1,bbox=[.1,.1,.4,.4])['face_id']
 def test_feedback_and_merge_roll_back_together_then_survive_reopen(self):
  a=self.face('a',[1,0]);b=self.face('b',[.99,.01])
  with patch.object(self.s,'_audit',side_effect=RuntimeError('interrupted')):
   with self.assertRaises(RuntimeError):self.s.merge_faces(a,b,'review',feedback=True)
  self.assertEqual(self.s.canonical_face(a),a);self.assertEqual(self.s.face_feedback(),[])
  self.s.merge_faces(a,b,'review',feedback=True);self.s.close();self.s=ProjectStore(self.path,'fixture')
  self.assertEqual(self.s.canonical_face(a),b);self.assertEqual(self.s.face_feedback()[0]['decision'],'same')
 def test_negative_feedback_blocks_automatic_regrouping(self):
  a=self.face('a',[1,0]);b=self.face('b',[.99,.01]);self.s.review_face_matching('different',a,b)
  self.assertEqual(regroup(self.s)['face_merges'],0)
  with self.assertRaisesRegex(ValueError,'different'):self.s.merge_faces(a,b,'Automatic grouping')
 def test_named_identity_competes_with_other_names_not_its_own_fragments(self):
  a=self.face('a',[1,0,0]);self.s.name_face(a,'Howard')
  b=self.face('b',[.77,.638,0]);c=self.face('c',[.775,.632,0])
  d=self.face('d',[0,0,1]);self.s.name_face(d,'Vince')
  result=regroup(self.s)
  self.assertGreaterEqual(result['face_merges'],2)
  self.assertEqual(self.s.canonical_face(b),self.s.canonical_face(a));self.assertEqual(self.s.canonical_face(c),self.s.canonical_face(a));self.assertNotEqual(self.s.canonical_face(d),self.s.canonical_face(a))
 def test_clean_face_voice_windows_require_independent_clips_and_reciprocal_support(self):
  state={'face_observations':[],'observations':[]}
  for i in range(6):
   clip=str(i//2);t=20*(i%2)+10
   state['face_observations'].append({'content_id':clip,'seconds':t,'face_id':'face','observation_id':str(i)})
   state['observations'].append({'content_id':clip,'start':t-1,'end':t+1,'person_id':'voice','observation_id':str(i)})
  p=proposals(state);self.assertEqual(p[0]['window_count'],6);self.assertTrue(p[0]['strong_suggestion'])
  state['face_observations'].append({'content_id':'0','seconds':10,'face_id':'other','observation_id':'other'})
  self.assertEqual(proposals(state)[0]['window_count'],5)
 def test_linked_name_and_rejected_voice_candidate_survive_restart(self):
  f=self.face('a',[1,0]);self.s.name_face(f,'Howard')
  p=self.s.provisional_speaker('a','speaker',0,4)['person_id']
  self.s.reject_voice_candidate(f,p);self.s.link_face_voice(f,p,'Operator listened to samples')
  self.assertEqual(next(x for x in self.s.people() if x['id']==p)['name'],'Howard')
  self.s.name_person(p,'Howard Moon')
  self.assertEqual(next(x for x in self.s.faces() if x['id']==f)['name'],'Howard Moon')
  self.s.close();self.s=ProjectStore(self.path,'fixture')
  self.assertEqual(self.s.faces()[0]['voice_link']['person_id'],p)
  self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM av_link_feedback').fetchone()[0],0)
 def test_automatic_note_inheritance_is_provenanced_and_removable(self):
  a=self.s.add_annotation('a','A note',metadata={'tags':['forest']})
  link=self.s.suggest_links('b',[1.,0.],{'a':{'vector':[1.,0.],'model_revision':'clip'}},'clip')[0]['id']
  n=self.s.accept_link(link,automatic=True)
  row=next(x for x in self.s.annotations() if x['id']==n)
  self.assertEqual(row['source'],'automatic_inheritance');self.assertEqual(row['metadata']['decision_source'],'automatic')
  self.s.remove_inherited_annotation(n)
  self.assertEqual(self.s.annotations()[0]['id'],a);self.assertEqual(self.s.links()[0]['status'],'rejected')

if __name__=='__main__':unittest.main()
