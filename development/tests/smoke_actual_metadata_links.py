"""CPU-only full candidate/suggestion path using already-computed real CLIP vectors."""
import json,os,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lab_indexer.pipeline import Pipeline
from lab_indexer.project_store import ProjectStore
from lab_indexer.search_projection import project_documents
from lab_indexer.atomic import atomic_json
SOURCE=ROOT/'projects/performance-b4f23e17';PROJECT=ROOT/'projects/metadata-link-smoke'
PROJECT.mkdir(exist_ok=True)
catalog=json.loads((SOURCE/'catalog.json').read_text());fingerprints=json.loads((SOURCE/'clip-fingerprints.json').read_text());keys=sorted(fingerprints)
if len(keys)<2:raise RuntimeError('Need two actual indexed clip fingerprints')
project_id='link-smoke-'+uuid.uuid4().hex;catalog['project']['id']=project_id
# Keep repeat invocations independent, preserving any previous smoke's audit evidence.
PROJECT=PROJECT/project_id;PROJECT.mkdir()
atomic_json(PROJECT/'clip-fingerprints.json',fingerprints)
with ProjectStore(PROJECT/'_LAB_NOTES/project.sqlite3',project_id=project_id) as store:
 source,target=keys[:2]
 annotation=store.add_annotation(source,'LAB TEST: prairie pickup note',start=10,end=20,metadata={'test_only':True,'tags':['pickup']})
 catalog['search_projection']=project_documents(catalog,store);atomic_json(PROJECT/'catalog.json',catalog)
 pipeline=object.__new__(Pipeline);pipeline.project=PROJECT
 oldpath=os.environ.get('PATH');os.environ['PATH']=str(ROOT/'bin')+':/usr/bin:/bin'
 try:
  started=time.perf_counter();result=pipeline._suggest_metadata(store,target);elapsed=time.perf_counter()-started
 finally:
  if oldpath is None:os.environ.pop('PATH',None)
  else:os.environ['PATH']=oldpath
 assert result['count']==1,result
 links=store.links(target,status='suggested');assert len(links)==1
 assert store.annotations(target)==[],'Suggestion must not silently inherit'
 accepted=store.accept_link(links[0]['id']);annotations=store.annotations(target)
 assert len(annotations)==1 and annotations[0]['id']==accepted
 assert annotations[0]['source']=='accepted_inheritance'
 assert annotations[0]['start'] is None and annotations[0]['end'] is None
 assert annotations[0]['metadata']['source_annotation_id']==annotation
 assert store.annotations(source)[0]['text']=='LAB TEST: prairie pickup note'
 projection=project_documents(catalog,store)
 assert any(d.get('source')=='accepted_inheritance' and 'LAB TEST' in d['text'] for d in projection['documents'])
 evidence={'passed':True,'project':str(PROJECT),'source_content':source,'target_content':target,'candidate_engine':'native Orama existing CLIP512 schema/index','real_precomputed_CLIP_vectors':True,'new_GPU_inference':False,'restricted_PATH':True,'node':str(ROOT/'bin/node'),'candidate_and_suggestion_seconds':elapsed,'cosine':links[0]['cosine'],'suggestion_only_before_acceptance':True,'operator_source_unchanged':True,'source_timestamps_not_inherited':True,'accepted_annotation_id':accepted,'projection_same_search_contract':True}
 atomic_json(ROOT/'architecture/metadata-link-smoke.json',evidence);print(json.dumps(evidence,indent=2))
