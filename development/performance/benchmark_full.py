#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys,time,uuid,traceback,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--gpu-authorized',action='store_true');a=ap.parse_args()
 if not a.gpu_authorized:ap.error('Parent GPU window required')
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',PATH=str(Path('/Volumes/ThunderBlade X8/AI Indexer/bin'))+':/usr/bin:/bin:/usr/sbin:/sbin')
 process_start=time.perf_counter()
 from lab_indexer.pipeline import Pipeline
 from lab_indexer.models import speaker_revision
 from lab_indexer.project_store import ProjectStore
 project=ROOT/'projects'/('performance-'+uuid.uuid4().hex[:8]);runs=[]
 report={'project':str(project),'runs':runs,'scope':'Full isolated pipeline on three fresh container SHAs with identical encoded AV streams. First run includes cold startup; same Pipeline retains models for subsequent runs. No analysis reuse. Not production trial.','cold_import_seconds':time.perf_counter()-process_start}
 out=ROOT/'benchmarks/full-pipeline.json'
 policy={'model_revision':speaker_revision(),'threshold':.70,'margin':.10,'calibration_id':'librispeech3speaker-smoke-20261101','production_approved':False}
 try:
  with Pipeline(project,audio_context=True,diarization=True,auto_match=True,policy=policy) as pipeline:
   for i in range(1,4):
    started=process_start if i==1 else time.perf_counter()
    r=pipeline.analyze(ROOT/'fixtures'/f'trailer-enhanced-{i}.mp4');wall=time.perf_counter()-started
    obj=project/'_DIT_NOTES/.objects'/r['content_id']/pipeline.profile
    result=json.loads((obj/'result.json').read_text())
    transcript=' '.join(t.get('text','').strip() for t in result['tracks']).strip()
    row={**r,'run':i,'state':'cold' if i==1 else 'resident','measured_wall_seconds':wall,'measured_ratio':wall/r['source_seconds'],'budget_seconds':.25*r['source_seconds'],'budget_pass':wall<=.25*r['source_seconds'],'transcript':transcript,'engine_timing':result['timing'],'diarization_timing':[t.get('diarization',{}).get('timing') for t in result['tracks']],'highlights':result['highlights']}
    with ProjectStore(project/'_LAB_NOTES/project.sqlite3') as store:
     row['people']=store.people()
     if i==1:
      if row['people']:store.name_person(row['people'][0]['id'],'Narrator (lab label)')
      store.add_annotation(r['content_id'],'Prairie trailer reference; operator-added lab annotation.',metadata={'fixture':'explicit operator entry'})
    runs.append(row);out.write_text(json.dumps(report,indent=2,default=str)+'\n');print(json.dumps({k:row[k] for k in ['run','state','measured_wall_seconds','measured_ratio','budget_pass','timing','diarization_timing','metadata_links']}),flush=True)
   report['all_transcripts_identical']=len({r['transcript'] for r in runs})==1
 except BaseException as e:
  report['error']=str(e);report['traceback']=traceback.format_exc();raise
 finally:report['wall_until_exit_seconds']=time.perf_counter()-process_start;out.write_text(json.dumps(report,indent=2,default=str)+'\n')
if __name__=='__main__':main()
