"""Replay real CPU face vectors through pipeline registry/projection. No MLX calls."""
import json,tempfile,uuid
from pathlib import Path
from lab_indexer.guards import ROOT
from lab_indexer.pipeline import Pipeline
from lab_indexer.project_store import ProjectStore
from lab_indexer.search_projection import project_documents
from lab_indexer.face_models import embedding_revision
from lab_indexer.atomic import atomic_json

def main():
 data=json.loads((ROOT/'benchmarks/faces-cpu.json').read_text())['portrait_runs'][0]
 policy={'auto_assign':True,'model_revision':embedding_revision(),'threshold':.8,'margin':.15,'calibration_id':'two-portrait-transforms-smoke-only'}
 project=ROOT/'projects'/('face-registry-smoke-'+uuid.uuid4().hex[:8])
 with Pipeline(project,faces=True,face_policy=policy) as pipeline,ProjectStore(project/'_LAB_NOTES/project.sqlite3') as store:
  first=pipeline._register_faces(store,'portrait-fixture-a',data,'fixture-profile')
  ids=sorted({r['face_id'] for r in first});assert len(ids)==2
  store.name_face(ids[0],'Face A (operator test label)')
  again=pipeline._register_faces(store,'portrait-fixture-b',data,'fixture-profile')
  assert {r['face_id'] for r in again}==set(ids)
  assert not any(f['voice_link'] for f in store.faces())
  voice=store.provisional_speaker('voice-fixture','voice0',0,3)['person_id']
  store.link_face_voice(ids[0],voice,'Operator explicitly linked test entities')
  assert any(f['voice_link'] and f['voice_link']['person_id']==voice for f in store.faces())
  catalog={'project':{'id':store.project_id},'assets':[{'id':'portrait-fixture-a','content_id':'portrait-fixture-a','name':'Portrait fixture','relative_path':'fixture','kind':'video','duration':10,'highlights':[{'seconds':r['seconds'],'note':'Face test fixture','image_url':'/notes/.objects/portrait-fixture-a/'+pipeline.profile+'/'+r['frame']} for r in data['observations']],'transcript':[],'metadata':{}}]}
  projected=project_documents(catalog,store)
  output={'project':str(project),'real_vector_source':'benchmarks/faces-cpu.json','separate_face_entities':len(ids),'same_faces_across_content_ids':True,'operator_name_preserved':any(f['name']=='Face A (operator test label)' for f in store.faces()),'no_inferred_voice_links':True,'explicit_voice_link_passed':True,'projection_document_count':len(projected['documents']),'scope':'Transformed same-source portraits; not independent-shot field validation. Real face vectors, CPU registry/projection replay, no GPU.'}
 atomic_json(ROOT/'benchmarks/face-registration-smoke.json',output);print(json.dumps(output,indent=2))
if __name__=='__main__':main()
