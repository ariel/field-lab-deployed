"""Face-only recovery keeps sealed media analysis and operator edits intact."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ditnotes import library,face_maintenance as maintenance
from ditnotes.project_store import ProjectStore

class FixtureEngine:
 def analyze(self,source,output):
  (output/'frames').mkdir();(output/'faces').mkdir()
  for name in ('known','missing'):(output/'frames'/f'{name}.jpg').write_bytes(name.encode())
  (output/'faces/known.jpg').write_bytes(b'crop')
  result={'status':'complete','duration':4,'probe':{'streams':[]},'tracks':[],'timing':{},
          'highlights':[{'seconds':i,'frame':f'frames/{name}.jpg','label':'Fixture'} for i,name in enumerate(('known','missing'))],
          'faces':{'observations':[{'seconds':0,'frame':'frames/known.jpg','crop':'faces/known.jpg','bbox':[.1,.1,.5,.5],'embedding':[1,0,0],'model_revision':'face-fixture','quality':1,'quality_components':{},'detection_id':'0-0'}]}}
  (output/'result.json').write_text(json.dumps(result))

class Detector:
 def __init__(self):self.calls=0
 def analyze(self,frames,output,*,input_root):
  self.calls+=1;(output/'faces').mkdir();(output/'faces/0-0.jpg').write_bytes(b'new crop')
  f=frames[0]
  return {'observations':[{'seconds':f['seconds'],'frame':f['frame'],'crop':'faces/0-0.jpg','bbox':[.1,.1,.5,.5],'embedding':[1,0,0],'model_revision':'face-fixture','quality':1,'quality_components':{},'detection_id':'0-0'}]}

class FaceMaintenance(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.project=Path(self.tmp.name).resolve()
  safety=patch('ditnotes.sqlite_safety.require_safe_sqlite');safety.start();self.addCleanup(safety.stop)
  clip=self.project/'clip.mp4';clip.write_bytes(b'original fixture');library.process(clip,self.project,engine=FixtureEngine())
  self.notes=self.project/'_DIT_NOTES';self.db=self.notes/'project.sqlite3';self.detector=Detector()
  with ProjectStore(self.db) as store:
   obs=store.face_observations()[0];self.content=obs['content_id'];self.original=dict(store.db.execute('select * from face_observations').fetchone());store.name_face(obs['face_id'],'Fixture subject')
   store.add_annotation(self.content,'Operator note');store.provisional_speaker(self.content,'voice0',0,2)
   self.protected={table:[tuple(r) for r in store.db.execute('select * from '+table)] for table in ('people','observations','annotations','face_voice_links')}
 def count(self):
  with ProjectStore(self.db) as store:return len(store.face_observations())
 def run_maintenance(self,**kwargs):
  # The grouping implementation is independently replay/calibration tested.
  with patch('ditnotes.identity_grouping.regroup',return_value={'face_merges':0,'voice_merges':0,'conflicts_skipped':0}):
   return maintenance.run(self.project,detector=self.detector,**kwargs)
 def test_plan_is_read_only_and_apply_preserves_old_evidence_and_operator_data(self):
  before={p.relative_to(self.notes):p.read_bytes() for p in (self.notes/'.objects').rglob('*') if p.is_file()}
  proposal=maintenance.plan(self.project);self.assertEqual(proposal['pending_frames'],1);self.assertFalse((self.notes/'face-maintenance').exists())
  result=self.run_maintenance(publisher=lambda project:None);self.assertEqual(result['phase'],'index_published');self.assertEqual(self.count(),2)
  with ProjectStore(self.db) as store:
   old=dict(store.db.execute('select * from face_observations where id=?',(self.original['id'],)).fetchone());self.assertEqual(old,self.original)
   for table,rows in self.protected.items():self.assertEqual([tuple(r) for r in store.db.execute('select * from '+table)],rows)
   self.assertTrue(all(not o['frame_ref'].startswith('/notes/face-maintenance') for o in store.face_observations()))
  self.assertEqual(before,{p.relative_to(self.notes):p.read_bytes() for p in (self.notes/'.objects').rglob('*') if p.is_file()})
  self.assertTrue(Path(result['backup']).is_file());self.run_maintenance(publisher=lambda project:None);self.assertEqual(self.count(),2);self.assertEqual(self.detector.calls,1)
 def test_interrupt_before_commit_rolls_back_and_reuses_published_crops(self):
  def stop(phase):
   if phase=='before_database_commit':raise KeyboardInterrupt('fixture stop')
  with self.assertRaises(KeyboardInterrupt):self.run_maintenance(checkpoint=stop)
  self.assertEqual(self.count(),1);self.run_maintenance();self.assertEqual(self.count(),2);self.assertEqual(self.detector.calls,1)
 def test_interrupt_after_commit_is_idempotent_before_manifest_checkpoint(self):
  def stop(phase):
   if phase=='database_committed':raise KeyboardInterrupt('fixture stop')
  with self.assertRaises(KeyboardInterrupt):self.run_maintenance(checkpoint=stop)
  self.assertEqual(self.count(),2);self.run_maintenance();self.assertEqual(self.count(),2);self.assertEqual(self.detector.calls,1)
 def test_search_failure_keeps_database_commit_and_resumes_only_publication(self):
  with self.assertRaisesRegex(RuntimeError,'search unavailable'):self.run_maintenance(publisher=lambda project:(_ for _ in ()).throw(RuntimeError('search unavailable')))
  self.assertEqual(self.count(),2);result=self.run_maintenance(publisher=lambda project:None);self.assertEqual(result['phase'],'index_published');self.assertEqual(self.detector.calls,1)
 def test_changed_sealed_frame_fails_before_any_detection(self):
  frame=next((self.notes/'.objects').rglob('missing.jpg'));frame.write_bytes(b'tampered')
  with self.assertRaisesRegex(ValueError,'valid sealed'):self.run_maintenance()
  self.assertEqual(self.detector.calls,0);self.assertEqual(self.count(),1)
 def test_missing_crop_does_not_commit_dangling_reference(self):
  original=self.detector.analyze
  def missing(frames,output,**kwargs):
   result=original(frames,output,**kwargs);(output/'faces/0-0.jpg').unlink();return result
  self.detector.analyze=missing
  with self.assertRaisesRegex(ValueError,'crop is not sealed'):self.run_maintenance()
  self.assertEqual(self.count(),1)
 def test_policy_change_before_commit_rolls_back(self):
  current=maintenance.policy_id();changed=False
  def policy():return 'changed' if changed else current
  def flip(phase):
   nonlocal changed
   if phase=='before_database_commit':changed=True
  with patch.object(maintenance,'policy_id',side_effect=policy),self.assertRaisesRegex(ValueError,'policy changed'):self.run_maintenance(checkpoint=flip)
  self.assertEqual(self.count(),1)
 def test_packet_input_binding_is_checked(self):
  original=self.detector.analyze
  def wrong(frames,output,**kwargs):
   result=original(frames,output,**kwargs);result['observations'][0]['seconds']=99;return result
  self.detector.analyze=wrong
  with self.assertRaisesRegex(ValueError,'does not match sealed input'):self.run_maintenance()
  self.assertEqual(self.count(),1)
 def test_fresh_published_crop_corruption_is_rejected(self):
  def corrupt(phase):
   if phase=='evidence_published':
    crop=next((self.notes/'face-maintenance').glob('*/evidence/*/faces/*.jpg'));crop.write_bytes(b'corrupted')
  with self.assertRaisesRegex(ValueError,'seal verification'):self.run_maintenance(checkpoint=corrupt)
  self.assertEqual(self.count(),1)
 def test_symlinked_journal_is_rejected(self):
  proposal=maintenance.plan(self.project);folder=self.notes/'face-maintenance'/proposal['job_id'];folder.mkdir(parents=True)
  outside=self.project/'outside.json';outside.write_text('{}');(folder/'status.json').symlink_to(outside)
  with self.assertRaisesRegex(ValueError,'symlink'):self.run_maintenance()
  self.assertEqual(outside.read_text(),'{}')
 def test_missing_project_does_not_create_replacement_directory(self):
  missing=self.project/'not-mounted'
  with self.assertRaises(ValueError):maintenance.run(missing)
  self.assertFalse(missing.exists())
 def test_symlinked_maintenance_folder_is_rejected(self):
  (self.notes/'face-maintenance').symlink_to(self.project,target_is_directory=True)
  with self.assertRaisesRegex(ValueError,'symlink'):self.run_maintenance()
  self.assertEqual(self.count(),1)
if __name__=='__main__':unittest.main()
