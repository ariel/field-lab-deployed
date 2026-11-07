"""Additive face-only maintenance of sealed stills; never rerun audio or captions."""
from __future__ import annotations
import hashlib,json,re,sqlite3,time,uuid
from pathlib import Path
from .atomic import atomic_json,fsync_dir,fsync_tree
from .library import _lock,_valid_object
from .project_store import ProjectStore
from .features import features


def _hash(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def _inside(root,relative):
 if root.is_symlink():raise ValueError('Face maintenance refuses symlink roots')
 relative=Path(relative)
 if relative.is_absolute() or '..' in relative.parts:raise ValueError('Invalid generated face path')
 current=root
 for part in relative.parts:
  current=current/part
  if current.is_symlink():raise ValueError('Face maintenance refuses symlinks')
 if not current.resolve().is_relative_to(root.resolve()):raise ValueError('Face path outside notes')
 return current


def policy_id():
 files=('faces.py','face_models.py','face_store.py','face_policy.py','identity_grouping.py','features.py')
 evidence={name:_hash(Path(__file__).parent/name) for name in files};evidence['settings']=features()
 return hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()[:20]


def plan(project):
 project=Path(project).expanduser().resolve();notes=project/'_DIT_NOTES'
 if notes.is_symlink() or not notes.is_dir():raise ValueError('Existing local notes required')
 state=json.loads(_inside(notes,'state.json').read_text());frames=[];clips=0
 with sqlite3.connect(_inside(notes,'project.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
  observed={(r[0],r[1]) for r in db.execute('SELECT content_id,frame_ref FROM face_observations')}
 for relative,record in sorted(state['paths'].items()):
  if record.get('status')!='ready':continue
  content,profile=record['sha256'],record['profile_id']
  if not re.fullmatch('[0-9a-f]{64}',content) or not re.fullmatch('[0-9a-f]{20}',profile):raise ValueError('Invalid sealed object identity')
  base=Path('.objects')/content/profile;obj=_inside(notes,base)
  if not _valid_object(obj,content,profile):raise ValueError('Face maintenance requires valid sealed analysis')
  result=json.loads((obj/'result.json').read_text());clips+=1
  for frame in result.get('highlights',[]):
   source=_inside(notes,base/frame['frame']);ref='/notes/'+(base/frame['frame']).as_posix()
   frames.append({'content_id':content,'profile_id':profile,'seconds':float(frame['seconds']),'frame':frame['frame'],
                  'source_ref':ref,'source_path':(base/frame['frame']).as_posix(),'sha256':_hash(source),
                  'has_face':(content,ref) in observed})
 policy=policy_id();identity={'policy_id':policy,'frames':[{k:v for k,v in f.items() if k!='has_face'} for f in frames]}
 job=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:24]
 return {'schema_version':1,'project':str(project),'job_id':job,'policy_id':policy,'ready_clips':clips,
         'selected_frames':len(frames),'pending_frames':sum(not f['has_face'] for f in frames),'frames':frames,
         'scope':'Only selected stills without any saved face observation; existing observations remain unchanged.'}


def _bundle_valid(folder):
 try:
  manifest=json.loads((folder/'bundle.json').read_text())
  return all(_hash(_inside(folder,name))==digest for name,digest in manifest['files'].items()) and 'detections.json' in manifest['files']
 except (ValueError,OSError,KeyError,TypeError):return False


def _backup(notes,job):
 folder=_inside(notes,'face-maintenance/backups');folder.mkdir(parents=True,exist_ok=True);fsync_dir(folder.parent)
 target=folder/(job+'-'+uuid.uuid4().hex+'.sqlite3')
 with sqlite3.connect(_inside(notes,'project.sqlite3').as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(target) as dest:
  source.backup(dest)
  if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Face maintenance backup failed integrity check')
 with target.open('rb') as handle:__import__('os').fsync(handle.fileno())
 fsync_dir(folder);return target.relative_to(notes).as_posix()


def run(project,*,detector=None,publisher=None,checkpoint=None):
 """Publish crops before one SQL commit; resume failed search publication safely."""
 project=Path(project).expanduser().resolve();notes=project/'_DIT_NOTES'
 if not project.is_dir() or notes.is_symlink() or not notes.is_dir():raise ValueError('Existing project notes required')
 checkpoint=checkpoint or (lambda phase:None)
 with _lock(notes):
  proposal=plan(project);job=proposal['job_id'];folder=_inside(notes,Path('face-maintenance')/job)
  folder.mkdir(parents=True,exist_ok=True);fsync_dir(folder.parent);fsync_dir(notes)
  journal=_inside(notes,folder.relative_to(notes)/'status.json');status=json.loads(journal.read_text()) if journal.exists() else {'job_id':job,'policy_id':proposal['policy_id'],'phase':'planned'}
  if not status.get('backup'):status['backup']=_backup(notes,job);atomic_json(journal,status)
  bundle=folder/'evidence'
  if not _bundle_valid(bundle):
   from .scratch import scratch_directory
   if bundle.exists():raise ValueError('Incomplete face evidence; preserve it for inspection')
   from .faces import FaceModels
   detector=detector or FaceModels();detections=[]
   with scratch_directory(dir=folder,prefix='.prepare-') as scratch:
    scratch=Path(scratch);by_clip={}
    for frame in proposal['frames']:
     if not frame['has_face']:by_clip.setdefault(frame['content_id'],[]).append(frame)
    for content,frames in by_clip.items():
     output=scratch/content;output.mkdir()
     packet=detector.analyze([{'seconds':f['seconds'],'frame':f['source_path']} for f in frames],output,input_root=notes)
     by_ref={f['source_path']:f for f in frames}
     for observation in packet['observations']:
      f=by_ref[observation['frame']]
      detections.append({'content_id':content,'source_ref':f['source_ref'],'source_sha256':f['sha256'],**observation,'crop':content+'/'+observation['crop']})
    atomic_json(scratch/'detections.json',{'job_id':job,'policy_id':proposal['policy_id'],'observations':detections})
    atomic_json(scratch/'bundle.json',{'files':{p.relative_to(scratch).as_posix():_hash(p) for p in scratch.rglob('*') if p.is_file() and p.name!='.DS_Store'}})
    fsync_tree(scratch);scratch.replace(bundle);fsync_dir(folder)
   checkpoint('evidence_published')
  if not _bundle_valid(bundle):raise ValueError('Face evidence failed seal verification')
  packet=json.loads((bundle/'detections.json').read_text())
  if packet['job_id']!=job or packet['policy_id']!=proposal['policy_id']:raise ValueError('Face evidence policy differs')
  bindings={f['source_ref']:f for f in proposal['frames']};sealed=json.loads((bundle/'bundle.json').read_text())['files'];seen=set()
  for observation in packet['observations']:
   f=bindings.get(observation['source_ref'])
   if not f or observation['content_id']!=f['content_id'] or observation['source_sha256']!=f['sha256'] or observation['seconds']!=f['seconds'] or observation['frame']!=f['source_path']:
    raise ValueError('Face observation does not match sealed input')
   crop=observation['crop']
   if crop not in sealed or not _inside(bundle,crop).is_file():raise ValueError('Face observation crop is not sealed')
   identity=(observation['content_id'],observation['source_ref'],observation['detection_id'],observation['model_revision'])
   if identity in seen:raise ValueError('Duplicate staged face observation')
   seen.add(identity)
  if policy_id()!=proposal['policy_id']:raise ValueError('Face policy changed during maintenance')
  for f in proposal['frames']:
   if _hash(_inside(notes,f['source_path']))!=f['sha256']:raise ValueError('Selected still changed during maintenance')
  with ProjectStore(notes/'project.sqlite3') as store:
   with store._transaction():
    prior=next((json.loads(r[0]) for r in store.db.execute("SELECT payload FROM audit WHERE operation='face_maintenance_applied'") if json.loads(r[0]).get('job_id')==job),None)
    if prior:applied=prior
    else:
     occupied={(r[0],r[1]) for r in store.db.execute('SELECT content_id,frame_ref FROM face_observations')};added=[]
     for observation in packet['observations']:
      if (observation['content_id'],observation['source_ref']) in occupied:continue
      row=store.assign_face(observation['content_id'],observation['seconds'],observation['embedding'],observation['model_revision'],observation['quality'],
             bbox=observation['bbox'],frame_ref=observation['source_ref'],crop_ref='/notes/'+(bundle.relative_to(notes)/observation['crop']).as_posix(),
             detection_id=observation['detection_id'],quality_components=observation['quality_components'],auto_assign=features()['automatic_face_grouping'],calibration_id=proposal['policy_id'])
      added.append(row['observation_id'])
     from .identity_grouping import regroup
     grouping=regroup(store,kinds=('face',))
     applied={'job_id':job,'policy_id':proposal['policy_id'],'added_observation_ids':added,'grouping':grouping,'at':time.time()}
     store._audit('face_maintenance_applied',applied);checkpoint('before_database_commit')
     if policy_id()!=proposal['policy_id']:raise ValueError('Face policy changed before commit')
     if not _bundle_valid(bundle):raise ValueError('Face evidence changed before commit')
   checkpoint('database_committed')
  status.update(phase='database_applied',**applied);atomic_json(journal,status)
 if publisher is not None:
  publisher(project);checkpoint('index_published');status['phase']='index_published';atomic_json(journal,status)
 return {**status,'ready_clips':proposal['ready_clips'],'selected_frames':proposal['selected_frames'],'backup':str(notes/status['backup'])}
