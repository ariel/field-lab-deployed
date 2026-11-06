import os,sys,json,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PATH='/Volumes/ThunderBlade X8/AI Indexer/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin')
def main():
 from lab_indexer.pipeline import Pipeline
 from lab_indexer.project_store import ProjectStore
 policy=json.loads((ROOT/'performance/speaker-policy-lab.json').read_text());project=ROOT/'projects'/('voice-quality-'+uuid.uuid4().hex[:8]);runs=[];started=time.perf_counter()
 with Pipeline(project,audio_context=False,diarization=True,auto_match=True,policy=policy) as pipeline:
  for i,name in enumerate(['cross-clip-a.wav','cross-clip-b.wav']):
   r=pipeline.analyze(ROOT/'fixtures'/name)
   with ProjectStore(project/'_LAB_NOTES/project.sqlite3') as store:
    people=store.people()
    if i==0:
     for n,p in enumerate(people):store.name_person(p['id'],f'Voice {n+1} (operator lab label)')
    runs.append({'clip':name,'result':r,'people':store.people(),'observations':store.observations(r['content_id'])})
   print(json.dumps({'clip':name,'people':len(runs[-1]['people']),'seconds':r['timing']['total_seconds']}),flush=True)
 result={'project':str(project),'runs':runs,'wall_seconds':time.perf_counter()-started,'scope':'Quality smoke while parent OffShoot copy may overlap; not a strict throughput measurement. Three real speakers, disjoint utterances across clips, explicit lab-only calibrated policy.'}
 result['same_people_ids']=set(p['id'] for p in runs[0]['people'])==set(p['id'] for p in runs[1]['people']);result['expected_three_people']=len(runs[1]['people'])==3;result['names_preserved']=all(p['name'] for p in runs[1]['people'])
 (ROOT/'benchmarks/global-voices.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='runs'}))
if __name__=='__main__':main()
