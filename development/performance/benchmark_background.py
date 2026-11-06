from __future__ import annotations
import argparse,json,os,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PATH='/Volumes/ThunderBlade X8/AI Indexer/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin')
def main():
 p=argparse.ArgumentParser();p.add_argument('--gpu-authorized',action='store_true');p.add_argument('--faces',action='store_true');a=p.parse_args()
 if not a.gpu_authorized:p.error('Parent GPU window required')
 from lab_indexer.background import BackgroundPipeline
 from lab_indexer.project_store import ProjectStore
 policy=json.loads((ROOT/'performance/speaker-policy-lab.json').read_text());project=ROOT/'projects'/('background-'+uuid.uuid4().hex[:8]);started=time.perf_counter();actor=BackgroundPipeline(project,audio_context=True,diarization=True,auto_match=True,policy=policy,faces=a.faces);construction=time.perf_counter()-started
 try:
  warm=actor.warmup.result(timeout=90);startup=time.perf_counter()-started
  before={'analysis_snapshots':len(list(project.glob('_DIT_NOTES/.objects/*/*/complete.json'))),'identity_store_exists':(project/'_LAB_NOTES/project.sqlite3').exists()}
  arrived=time.perf_counter();run=actor.analyze(ROOT/'fixtures/trailer-baseline.mp4').result(timeout=90);arrival_wall=time.perf_counter()-arrived
  with ProjectStore(project/'_LAB_NOTES/project.sqlite3') as store:people=store.people()
  r=run['result'];payload={'project':str(project),'constructor_seconds':construction,'startup_wall_seconds':startup,'warmup':warm,'before_first_input':before,'input_arrived_after_warmup':True,'arrival_to_durable_output_seconds':arrival_wall,'queue_wait_seconds':run['queue_wait_seconds'],'processing_seconds':run['processing_seconds'],'result':r,'footage_ratio_including_residual_queue_wait':arrival_wall/r['source_seconds'],'budget_pass':arrival_wall<=.25*r['source_seconds'],'people':people,'scope':'Fresh first clip after representative background prewarm completes. Startup is reported separately; this does not claim cold launch under0.25x. All ASR/VLM/diarization/ECAPA/registry/index and durable publication included.'}
  (ROOT/'benchmarks'/('background-faces.json' if a.faces else 'background-pipeline.json')).write_text(json.dumps(payload,indent=2));print(json.dumps(payload),flush=True)
 finally:actor.close()
if __name__=='__main__':main()
