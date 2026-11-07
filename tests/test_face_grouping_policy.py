"""Anonymous face ambiguity, drift bounds and operator constraints."""
import json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ditnotes.project_store import ProjectStore
from ditnotes.identity_grouping import regroup
from ditnotes.face_policy import POLICY_ID

class FaceGroupingPolicy(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'registry.sqlite3';self.store=ProjectStore(self.path,'fixture');self.number=0
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def vector(self,degrees):return [math.cos(math.radians(degrees)),math.sin(math.radians(degrees))]
 def face(self,vector,*,clip=None,seconds=1,detection='0',revision='fixture',auto=False,**kwargs):
  self.number+=1
  return self.store.assign_face(clip or str(self.number),seconds,vector,revision,1,bbox=[.1,.1,.4,.4],detection_id=detection,auto_assign=auto,**kwargs)['face_id']
 def active(self):return [f for f in self.store.faces() if not f['merged_into']]
 def test_compatible_anonymous_fragments_are_not_artificial_rivals(self):
  ids=[self.face(self.vector(a)) for a in (0,10,12)]
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],2)
  self.assertEqual(len({self.store.canonical_face(f) for f in ids}),1)
 def test_incompatible_near_tied_rivals_abstain_from_both_directions(self):
  self.face(self.vector(0));self.face(self.vector(45));self.face(self.vector(-45))
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
  self.assertEqual(len(self.active()),3)
 def test_centroid_drift_does_not_bridge_incompatible_members(self):
  a=self.face(self.vector(0));b=self.face(self.vector(40));self.store.merge_faces(b,a,'Fixture historical cluster')
  c=self.face(self.vector(65),auto=True)
  self.assertNotEqual(c,a)
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
 def test_unenrolled_clean_samples_still_bound_cluster_support(self):
  a=self.face(self.vector(0));b=self.face(self.vector(90));self.store.merge_faces(b,a,'Operator fixture')
  self.store.db.execute('UPDATE face_observations SET enrolled=0 WHERE face_id=? AND content_id=?',(a,'2'));self.store.db.commit();self.store._refresh_face_profiles(a)
  self.assertNotEqual(self.face(self.vector(0),auto=True),a)
 def test_co_visible_faces_never_merge(self):
  self.face(self.vector(0),clip='same',detection='a');self.face(self.vector(1),clip='same',detection='b')
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
 def test_operator_different_feedback_remains_hard_exclusion(self):
  a=self.face(self.vector(0));b=self.face(self.vector(1));self.store.review_face_matching('different',a,b)
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
 def test_conflicting_names_remain_separate(self):
  a=self.face(self.vector(0));b=self.face(self.vector(1));self.store.name_face(a,'Person A');self.store.name_face(b,'Person B')
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
 def test_conflicting_operator_voice_links_remain_separate(self):
  a=self.face(self.vector(0));b=self.face(self.vector(1));pa=self.store.provisional_speaker('a','s',0,3)['person_id'];pb=self.store.provisional_speaker('b','s',0,3)['person_id']
  self.store.link_face_voice(a,pa,'Fixture');self.store.link_face_voice(b,pb,'Fixture')
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
 def test_explicit_threshold_is_preserved(self):
  a=self.face(self.vector(0));b=self.face(self.vector(30),auto=True,match_threshold=.95)
  self.assertNotEqual(a,b)
 def test_default_assignment_uses_tuned_threshold(self):
  a=self.face(self.vector(0));self.assertEqual(self.face(self.vector(30),auto=True),a)
 def test_default_named_assignment_retains_stricter_named_threshold(self):
  a=self.face(self.vector(0));self.store.name_face(a,'Person A')
  self.assertNotEqual(self.face(self.vector(45),auto=True),a)
  audit=json.loads(self.store.db.execute("SELECT payload FROM audit WHERE operation='face_observed' ORDER BY id DESC LIMIT 1").fetchone()[0]);self.assertEqual(audit['policy']['threshold'],.72)
  b=self.face(self.vector(0),revision='explicit');self.store.name_face(b,'Person B')
  self.assertEqual(self.face(self.vector(45),revision='explicit',auto=True,match_threshold=.65),b)
 def test_face_only_grouping_does_not_touch_voices(self):
  for c in ('a','b'):self.store.assign_speaker(c,'s',0,4,[1,0],'speaker',1,auto_assign=False)
  before=self.store.people();self.face(self.vector(0));self.face(self.vector(1))
  self.assertEqual(regroup(self.store,kinds=('face',))['voice_merges'],0);self.assertEqual(self.store.people(),before)
 def test_embedding_namespaces_remain_separate(self):
  self.face(self.vector(0),revision='one');self.face(self.vector(0),revision='two')
  self.assertEqual(regroup(self.store,kinds=('face',))['face_merges'],0)
 def test_interrupted_merge_rolls_back_and_reopens(self):
  a=self.face(self.vector(0));b=self.face(self.vector(1))
  with patch.object(self.store,'_audit',side_effect=RuntimeError('Interrupted')):
   with self.assertRaises(RuntimeError):regroup(self.store,kinds=('face',))
  self.store.close();self.store=ProjectStore(self.path,'fixture')
  self.assertNotEqual(self.store.canonical_face(a),self.store.canonical_face(b));self.assertEqual(self.store.db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
 def test_policy_identity_is_audited_separately_from_embedding_namespace(self):
  self.face(self.vector(0));self.face(self.vector(1));regroup(self.store,kinds=('face',))
  events=[dict(r) for r in self.store.db.execute("SELECT * FROM audit WHERE operation='faces_merged'")]
  self.assertTrue(events);self.assertIn(POLICY_ID,events[-1]['payload'])
 def test_invalid_domain_selector_rejected(self):
  for kinds in ((),('bogus',),('face','face')):
   with self.assertRaises(ValueError):regroup(self.store,kinds=kinds)

if __name__=='__main__':unittest.main()
