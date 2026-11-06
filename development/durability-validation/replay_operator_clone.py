"""Never writes canonical project; replay sealed AI into an SQLite-backup clone."""
from pathlib import Path
import sys,sqlite3,json,uuid,time
CANONICAL=Path('/Volumes/ThunderBlade X8/AI Indexer');LAB=Path('/Volumes/ThunderBlade X8/AI Indexer Lab');sys.path.insert(0,str(CANONICAL));from ditnotes.enrichment import register_result
SOURCE=Path('/Volumes/ThunderBlade X8/Ingests');folder=LAB/'durability-validation';clone=folder/('replay-'+uuid.uuid4().hex[:8]);notes=clone/'_DIT_NOTES';notes.mkdir(parents=True);snapshot=folder/'operator-edits-snapshot.sqlite3'
with sqlite3.connect('file:'+str(snapshot)+'?mode=ro',uri=True) as src,sqlite3.connect(notes/'project.sqlite3') as dst:src.backup(dst)
def state():
 with sqlite3.connect(notes/'project.sqlite3') as db:
  db.row_factory=sqlite3.Row
  return {'named_faces':[dict(r) for r in db.execute('SELECT * FROM faces WHERE name IS NOT NULL')],'voice_links':[dict(r) for r in db.execute('SELECT * FROM face_voice_links')],'named_voices':[dict(r) for r in db.execute('SELECT * FROM people WHERE name IS NOT NULL')],'annotations':[dict(r) for r in db.execute('SELECT * FROM annotations')],'meta':dict(db.execute('SELECT key,value FROM meta')),'observations':db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],'face_observations':db.execute('SELECT COUNT(*) FROM face_observations').fetchone()[0],'audit':db.execute('SELECT COUNT(*) FROM audit').fetchone()[0]}
before=state();identity=json.loads((SOURCE/'_DIT_NOTES/project.json').read_text());runs=[]
for path in sorted((SOURCE/'_DIT_NOTES/.objects').glob('*/56d9aa54e27c8b1d9d80/result.json')):
 result=json.loads(path.read_text());runs.append(register_result(clone,identity,path.parent.parent.name,result,path.parent.name))
after=state();passed=before==after
report={'passed':passed,'clone':str(clone),'replayed_clips':len(runs),'state_unchanged':passed,'before':before,'after':after,'scope':'Cloned user revision22; original canonical registry untouched. Tests registration/reconcile preservation, not abrupt power-loss hardware behavior.'};(folder/'operator-replay-evidence.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':passed,'clone':str(clone),'replayed_clips':len(runs),'before_revision':before['meta']['edit_revision'],'after_revision':after['meta']['edit_revision'],'ariel_preserved':before['named_faces']==after['named_faces'],'explicit_voice_link_preserved':before['voice_links']==after['voice_links'],'observations_before_after':[before['observations'],after['observations']],'faces_before_after':[before['face_observations'],after['face_observations']]}))
raise SystemExit(0 if passed else 1)
