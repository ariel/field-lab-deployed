"""Fixture-only fault tests. Never opens the real project database."""
import sys,os,json,time,signal,subprocess,tempfile,unittest,threading,sqlite3,select
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
RUNTIME=Path('/Volumes/ThunderBlade X8/AI Indexer');PYTHON=Path(os.environ.get('DURABILITY_PYTHON',str(RUNTIME/'.venv/bin/python')));BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(RUNTIME))
from ditnotes.project_store import ProjectStore
from ditnotes.enrichment import migrate_store,publish_index
from ditnotes.atomic import atomic_json
from ditnotes.catalog_index import read_snapshot
OPS=['voice_name','face_name','link','unlink','note_update','inherit_accept','voice_merge','face_merge']

def setup(project):
 project=Path(project);db=project/'_DIT_NOTES/project.sqlite3'
 with ProjectStore(db,'fixture-project') as s:
  p1=s.provisional_speaker('clip-a','a',0,3)['person_id'];p2=s.provisional_speaker('clip-b','b',0,3)['person_id']
  s.name_person(p1,'Original voice')
  f1=s.assign_face('clip-a',1,[1.,0.],'fixture-face',1,bbox=[.1,.1,.8,.8],detection_id='a')['face_id']
  f2=s.assign_face('clip-b',1,[0.,1.],'fixture-face',1,bbox=[.1,.1,.8,.8],detection_id='b')['face_id'];s.name_face(f1,'Original face')
  note=s.add_annotation('clip-a','Original note',metadata={'tags':['original']})
  link=s.suggest_links('clip-b',[1.,0.],{'clip-a':{'vector':[1.,0.],'model_revision':'fixture-clip'}},'fixture-clip')[0]['id']
  s.update_annotation(note,'Edited source after proposal',metadata={'tags':['edited']})
  ids=dict(p1=p1,p2=p2,f1=f1,f2=f2,note=note,link=link)
 atomic_json(project/'ids.json',ids)
 return db,ids

def apply(s,ids,operation):
 if operation=='voice_name':s.name_person(ids['p1'],'Committed voice')
 elif operation=='face_name':s.name_face(ids['f1'],'Committed face')
 elif operation=='link':s.link_face_voice(ids['f1'],ids['p1'],'Explicit fixture link')
 elif operation=='unlink':s.unlink_face_voice(ids['f1'],'Explicit fixture unlink')
 elif operation=='note_update':s.update_annotation(ids['note'],'Committed note',metadata={'tags':['committed']})
 elif operation=='inherit_accept':s.accept_link(ids['link'])
 elif operation=='voice_merge':s.merge_people(ids['p2'],ids['p1'],'Explicit fixture merge',chosen_name='Merged voice')
 elif operation=='face_merge':s.merge_faces(ids['f2'],ids['f1'],'Explicit fixture merge',chosen_name='Merged face')
 else:raise ValueError(operation)

def view(db):
 with ProjectStore(db) as s:
  return {'revision':s.edit_revision,'indexed':s.indexed_edit_revision,'people':s.people(),'faces':s.faces(),'annotations':s.annotations(),'links':s.links(),'audit':s.audit()}

def child(project,operation,point):
 ids=json.loads((project/'ids.json').read_text())
 with ProjectStore(project/'_DIT_NOTES/project.sqlite3') as s:
  if point.startswith('mid'):
   original_audit=s._audit
   def paused(*a,**k):
    if point=='mid_audit':original_audit(*a,**k)
    print('MID',flush=True);threading.Event().wait(60)
   s._audit=paused
  apply(s,ids,operation)
  print('COMMITTED',flush=True);threading.Event().wait(60)

class DurabilityTests(unittest.TestCase):
 def test_sqlite_version_guard(self):
  from ditnotes.sqlite_safety import version_supported,require_safe_sqlite
  for version in ['3.50.4','3.51.2','3.44.5','3.45.1','invalid','3.51','-1.51.3']:
   self.assertFalse(version_supported(version),version)
  for version in ['3.51.3','3.53.1','3.50.7','3.50.8','3.44.6']:
   self.assertTrue(version_supported(version),version)
  with patch('ditnotes.sqlite_safety.sqlite3.sqlite_version','3.50.4'):
   with self.assertRaises(RuntimeError):require_safe_sqlite()
 def temp(self):return tempfile.TemporaryDirectory(prefix='fault-',dir=BASE)
 def assert_integrity(self,db):
  with sqlite3.connect(db) as conn:self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertFalse(conn.execute('PRAGMA foreign_key_check').fetchall())
 def run_fault(self,project,operation,point):
  proc=subprocess.Popen([str(PYTHON),str(Path(__file__).resolve()),'--child',str(project),operation,point],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  try:
   ready,_,_=select.select([proc.stdout],[],[],15)
   self.assertTrue(ready,'Child did not reach fault point')
   line=proc.stdout.readline().strip()
   self.assertEqual(line,'MID' if point.startswith('mid') else 'COMMITTED',proc.stderr.read() if proc.poll() is not None else line)
   proc.kill();proc.wait(timeout=5)
  finally:
   if proc.poll() is None:proc.kill();proc.wait(timeout=5)
   proc.stdout.close();proc.stderr.close()
 def test_committed_edits_survive_sigkill_with_wal_open(self):
  for operation in OPS:
   with self.subTest(operation=operation),self.temp() as folder:
    project=Path(folder);db,ids=setup(project)
    if operation=='unlink':
     with ProjectStore(db) as s:s.link_face_voice(ids['f1'],ids['p1'],'Initial fixture link')
    before=view(db);self.run_fault(project,operation,'committed');after=view(db);self.assert_integrity(db)
    self.assertEqual(after['revision'],before['revision']+1);self.assertEqual(len(after['audit']),len(before['audit'])+1)
    if operation=='voice_name':self.assertEqual(next(p for p in after['people'] if p['id']==ids['p1'])['name'],'Committed voice')
    if operation=='face_name':self.assertEqual(next(p for p in after['faces'] if p['id']==ids['f1'])['name'],'Committed face')
    if operation=='link':self.assertEqual(next(p for p in after['faces'] if p['id']==ids['f1'])['voice_link']['person_id'],ids['p1'])
    if operation=='unlink':self.assertIsNone(next(p for p in after['faces'] if p['id']==ids['f1'])['voice_link'])
    if operation=='note_update':self.assertEqual(after['annotations'][0]['text'],'Committed note');self.assertEqual(after['annotations'][0]['metadata']['tags'],['committed'])
    if operation=='inherit_accept':
     inherited=next(a for a in after['annotations'] if a['source']=='accepted_inheritance');self.assertEqual(inherited['text'],'Original note');self.assertEqual(inherited['metadata']['suggested_metadata']['tags'],['original']);self.assertEqual(inherited['source_id'],ids['link']);self.assertIsNone(inherited['start']);self.assertIsNone(inherited['end'])
    if operation=='voice_merge':self.assertEqual(next(p for p in after['people'] if p['id']==ids['p2'])['merged_into'],ids['p1'])
    if operation=='face_merge':self.assertEqual(next(p for p in after['faces'] if p['id']==ids['f2'])['merged_into'],ids['f1'])
 def test_mid_transaction_kill_rolls_back_mutation_audit_revision(self):
  for operation in OPS:
   for point in ('mid','mid_audit'):
    with self.subTest(operation=operation,point=point),self.temp() as folder:
     project=Path(folder);db,ids=setup(project)
     if operation=='unlink':
      with ProjectStore(db) as s:s.link_face_voice(ids['f1'],ids['p1'],'Initial fixture link')
     before=view(db);self.run_fault(project,operation,point);after=view(db);self.assertEqual(after,before);self.assert_integrity(db)
 def test_pragmas_directory_sync_and_same_identity_concurrent_initialization(self):
  with self.temp() as folder:
   db=Path(folder)/'new/nested/project.sqlite3'
   with ThreadPoolExecutor(8) as pool:ids=list(pool.map(lambda _ : self.open_id(db),range(8)))
   self.assertEqual(len(set(ids)),1)
   calls=[]
   from ditnotes.atomic import fsync_dir as real_sync
   with patch('ditnotes.project_store.fsync_dir',side_effect=lambda p:(calls.append(str(p)),real_sync(p))):
    with ProjectStore(db) as s:
     self.assertEqual(s.db.execute('PRAGMA journal_mode').fetchone()[0],'wal')
     for name,want in [('synchronous',2),('fullfsync',1),('checkpoint_fullfsync',1)]:self.assertEqual(s.db.execute('PRAGMA '+name).fetchone()[0],want)
     p=s.provisional_speaker('a','a',0,2)['person_id'];n=len(calls);s.name_person(p,'Saved');self.assertGreater(len(calls),n)
   self.assertIn(str(db.parent),calls);self.assert_integrity(db)
 def open_id(self,db):
  with ProjectStore(db) as s:return s.project_id
 def test_legacy_backup_includes_wal_and_never_overwrites_new_canonical_edits(self):
  with self.temp() as folder:
   project=Path(folder);old=project/'_LAB_NOTES/project.sqlite3'
   with ProjectStore(old,'legacy') as legacy:
    voice=legacy.provisional_speaker('a','a',0,2)['person_id'];legacy.name_person(voice,'Legacy committed WAL name')
    target=migrate_store(project)
    with ProjectStore(target) as new:self.assertEqual(new.people()[0]['name'],'Legacy committed WAL name')
  with self.temp() as folder:
   project=Path(folder);old=project/'_LAB_NOTES/project.sqlite3'
   with ProjectStore(old,'legacy') as legacy:legacy.provisional_speaker('a','a',0,2)
   reached=threading.Event();release=threading.Event();real_link=os.link
   def delayed_link(a,b):reached.set();release.wait(5);return real_link(a,b)
   with patch('ditnotes.enrichment.os.link',side_effect=delayed_link),ThreadPoolExecutor(1) as pool:
    future=pool.submit(migrate_store,project);self.assertTrue(reached.wait(5))
    with ProjectStore(project/'_DIT_NOTES/project.sqlite3','new-live-project') as live:
     pid=live.provisional_speaker('new','new',0,2)['person_id'];live.name_person(pid,'New canonical edit wins')
    release.set();future.result(timeout=5)
   with ProjectStore(project/'_DIT_NOTES/project.sqlite3') as live:self.assertEqual(live.project_id,'new-live-project');self.assertEqual(live.people()[0]['name'],'New canonical edit wins')
 def test_concurrent_index_snapshot_cannot_erase_new_operator_commit(self):
  with self.temp() as folder:
   project=Path(folder);db,ids=setup(project);entered=threading.Event();release=threading.Event()
   catalog={'project':{'id':'fixture-project'},'assets':[{'id':'asset','content_id':'clip-a','name':'Fixture','relative_path':'fixture.mp4','kind':'video','highlights':[],'transcript':[{'start':0,'end':3,'text':'Fixture transcript'}]}]};atomic_json(project/'_DIT_NOTES/catalog.json',catalog)
   class Backend:
    executor=ThreadPoolExecutor(1)
    def readiness(self):return {'ready':True,'revision':{'text':'fixture-text','clip':'fixture-clip','reranker':'fixture-rerank'}}
    def _infer(self,action,values,query):
     entered.set();release.wait(5);return {'vectors':[[1/(384**.5)]*384 for _ in values]}
   backend=Backend()
   try:
    with ThreadPoolExecutor(1) as pool:
     future=pool.submit(publish_index,project,backend);self.assertTrue(entered.wait(5))
     with ProjectStore(db) as writer:writer.update_annotation(ids['note'],'Committed while indexing',metadata={'tags':['new']});writer.name_person(ids['p1'],'New concurrent name');new_revision=writer.edit_revision
     release.set();future.result(timeout=10)
    with ProjectStore(db) as s:self.assertEqual(s.annotations()[0]['text'],'Committed while indexing');self.assertEqual(s.edit_revision,new_revision);self.assertLess(s.indexed_edit_revision,s.edit_revision)
    publish_index(project,backend)
    with ProjectStore(db) as s:self.assertEqual(s.edit_revision,s.indexed_edit_revision)
    docs=read_snapshot(project)['catalog']['search_projection']['documents'];self.assertTrue(any('Committed while indexing' in d['text'] for d in docs));self.assertTrue(any('New concurrent name' in d['personNames'] for d in docs))
   finally:release.set();backend.executor.shutdown()

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),sys.argv[3],sys.argv[4])
 else:unittest.main()
