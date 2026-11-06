"""Project annotations on the existing local server and Orama projection."""
from __future__ import annotations
import copy,json,threading
from urllib.parse import urlsplit
from .project_store import ProjectStore
from .search_projection import project_documents

class MetadataAPI:
 def __init__(self,server):
  self.server=server;self.stop=threading.Event();self.changed=threading.Event();self.error=None
  self.thread=threading.Thread(target=self._loop,name='annotation-index',daemon=True);self.thread.start()
  if (server.project/'_DIT_NOTES/project.sqlite3').is_file():self.changed.set()
 def close(self):self.stop.set();self.changed.set();self.thread.join(timeout=2)
 def store(self,catalog=None):
  catalog=self.server.catalog.read() if catalog is None else catalog
  identity=catalog.get('project',{}).get('id')
  if identity=='waiting-for-ingest':raise ValueError('No indexed clips yet')
  return ProjectStore(self.server.project/'_DIT_NOTES/project.sqlite3',project_id=identity)
 def catalog(self):
  # Catalog and vectors remain one sealed publication; edits are immediately
  # visible in metadata state while the shared index catches up atomically.
  return self.server.catalog.read()
 def state(self):
  if not (self.server.project/'_DIT_NOTES/project.sqlite3').is_file() and not self.server.catalog.read().get('assets'):
   return {'people':[],'observations':[],'faces':[],'face_observations':[],'annotations':[],'links':[],'edit_revision':0,'indexed_edit_revision':0,'index_error':None}
  with self.store() as store:
   # A controller publication may resolve our revision gap after a retry failed.
   if store.edit_revision<=store.indexed_edit_revision:self.error=None
   return {'people':store.people(),'observations':[{k:v for k,v in o.items() if k!='embedding'} for o in store.observations()],'faces':store.faces(),'face_observations':[{k:v for k,v in o.items() if k!='embedding'} for o in store.face_observations()],'annotations':store.annotations(),'links':store.links(status='suggested'),'edit_revision':store.edit_revision,'indexed_edit_revision':store.indexed_edit_revision,'index_error':self.error}
 def face_review(self):
  import numpy as np
  from .features import features
  state=self.state();suggestions={}
  with self.store() as s:
   active={f['id'] for f in state['faces'] if not f['merged_into']}
   rows=[dict(r) for r in s.db.execute('SELECT * FROM face_profiles') if r['face_id'] in active]
   for a in rows:
    scores=[];av=np.array(json.loads(a['centroid']))
    for b in rows:
     if a['face_id']==b['face_id'] or a['model_revision']!=b['model_revision'] or a['dimension']!=b['dimension']:continue
     if s.faces_marked_different(a['face_id'],b['face_id']):continue
     scores.append({'face_id':b['face_id'],'cosine':float(av@np.array(json.loads(b['centroid'])))})
    suggestions[a['face_id']]=sorted(scores,key=lambda r:-r['cosine'])[:6]
   feedback=s.face_feedback()
   rejected={(s.canonical_face(r['face_id']),s.canonical_person(r['person_id'])) for r in s.db.execute("SELECT * FROM av_link_feedback WHERE decision='rejected'")}
  from .av_links import proposals
  av=[r for r in proposals(state) if (r['face_id'],r['person_id']) not in rejected]
  return {**state,'similar_faces':suggestions,'matching_feedback':feedback,'voice_candidates':av,'features':features()}
 def mutate(self,path,v):
  with self.store() as s:
   if path=='/api/name':s.name_person(v['person_id'],v.get('name') or None);result={'saved':True}
   elif path=='/api/face/name':s.name_face(v['face_id'],v.get('name') or None);result={'saved':True}
   elif path=='/api/face/link':s.link_face_voice(v['face_id'],v['person_id'],v.get('reason') or 'Operator verified face and voice');result={'saved':True}
   elif path=='/api/face/unlink':s.unlink_face_voice(v['face_id'],v.get('reason') or 'Operator removed face and voice link');result={'saved':True}
   elif path=='/api/people/merge':result={'person_id':s.merge_people(v['source_id'],v['target_id'],v.get('reason') or 'Operator confirmed same voice',chosen_name=v.get('chosen_name'))}
   elif path=='/api/face/merge':result={'face_id':s.merge_faces(v['source_id'],v['target_id'],v.get('reason') or 'Operator confirmed same face',chosen_name=v.get('chosen_name'))}
   elif path=='/api/face/review':
    if v['decision']=='same':result={'face_id':s.merge_faces(v['face_a'],v['face_b'],'Operator confirmed same person in face review',chosen_name=v.get('chosen_name'),feedback=True)}
    else:result={'feedback_id':s.review_face_matching(v['decision'],v.get('face_a'),v.get('face_b'),v.get('comment',''))}
   elif path=='/api/face/reject-voice':s.reject_voice_candidate(v['face_id'],v['person_id']);result={'saved':True}
   elif path=='/api/people/split':result={'person_id':s.split_person(v['person_id'],v['observation_ids'],v['reason'],new_name=v.get('new_name'))}
   elif path=='/api/face/split':result={'face_id':s.split_face(v['face_id'],v['observation_ids'],v['reason'],new_name=v.get('new_name'))}
   elif path=='/api/annotation':
    known={a.get('content_id') or a['id'] for a in self.server.catalog.read().get('assets',[])}
    if v['content_id'] not in known:raise ValueError('Clip is not in the project')
    result={'annotation_id':s.add_annotation(v['content_id'],v['text'],start=v.get('start'),end=v.get('end'),metadata=v.get('metadata'))}
   elif path=='/api/annotation/update':s.update_annotation(v['annotation_id'],v['text'],metadata=v.get('metadata'));result={'saved':True}
   elif path=='/api/annotation/remove-inherited':s.remove_inherited_annotation(v['annotation_id']);result={'saved':True}
   elif path=='/api/link/accept':result={'annotation_id':s.accept_link(v['link_id'])}
   elif path=='/api/link/reject':s.reject_link(v['link_id']);result={'saved':True}
   else:raise KeyError('Unknown metadata action')
  self.changed.set();return result
 def _loop(self):
  while not self.stop.is_set():
   self.changed.wait(2)
   if self.stop.is_set():break
   self.changed.clear()
   try:
    if not (self.server.project/'_DIT_NOTES/project.sqlite3').is_file():continue
    with self.store() as store:pending=store.edit_revision>store.indexed_edit_revision
    if not pending:
     self.error=None
     continue
    if self.stop.wait(.3):break
    from .enrichment import publish_index
    publish_index(self.server.project,self.server.search_backend)
    self.error=None
   except Exception as e:
    # The ingest controller owns this same project lock while publishing.
    # Normal contention is retryable updating work, not a failed index.
    self.error=None if isinstance(e,RuntimeError) and str(e)=='Another process is updating this project' else str(e)
    # Revision gap is durable; retry periodically without dropping edits.
    if self.stop.wait(5):break

ACTIONS={'/api/face/reject-voice','/api/face/review','/api/people/merge','/api/face/merge','/api/people/split','/api/face/split','/api/name','/api/face/name','/api/face/link','/api/face/unlink','/api/annotation','/api/annotation/update','/api/annotation/remove-inherited','/api/link/accept','/api/link/reject'}
def handle_post(handler):
 path=urlsplit(handler.path).path
 if path not in ACTIONS:return False
 host=handler.headers.get('Host','');origin=handler.headers.get('Origin');port=handler.server.server_port
 if host not in (f'127.0.0.1:{port}',f'localhost:{port}') or origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
  handler.send_error(403);return True
 if handler.headers.get('Content-Type','').split(';')[0]!='application/json':handler.send_error(415);return True
 try:
  length=int(handler.headers.get('Content-Length','0'))
  if not 0<length<=1024*1024:raise ValueError('Invalid request size')
  values=json.loads(handler.rfile.read(length))
  if not isinstance(values,dict):raise ValueError('Expected a JSON object')
  handler._json(handler.server.metadata.mutate(path,values),False)
 except Exception as e:handler._json({'error':str(e)},False,400)
 return True
