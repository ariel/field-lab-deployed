"""Isolated, resumable long-media torture-test driver; production ingest unchanged."""
import json,math,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')

def main():
 from ditnotes.atomic import atomic_json
 from ditnotes.engine import Engine
 from ditnotes.library import process
 from ditnotes.search_backend import SearchBackend
 from ditnotes.enrichment import publish_index
 source=Path('/Users/mattb/Movies/boosh.mp4');project=Path('/Users/mattb/Movies/BooshTest')
 staging=project/'preparation';media=project/'media';notes=project/'_DIT_NOTES'
 for p in (staging,media,notes):p.mkdir(parents=True,exist_ok=True)
 duration=float(json.loads(subprocess.check_output([str(ROOT/'bin/ffprobe'),'-v','error','-show_entries','format=duration','-of','json',str(source)]))['format']['duration'])
 previous=json.loads((project/'test-status.json').read_text()) if (project/'test-status.json').exists() else {}
 started=previous.get('started_at',time.time());status={'source':str(source),'source_duration':duration,'started_at':started,'completed':0,'total':math.ceil(duration/300),'parts':[]}
 def update(stage,**values):
  status.update(stage=stage,updated_at=time.time(),elapsed=time.time()-started,**values)
  atomic_json(project/'test-status.json',status)
  print(json.dumps({'stage':stage,**values,'elapsed':round(time.time()-started,1)}),flush=True)
 if not (notes/'project.json').exists():atomic_json(notes/'project.json',{'id':uuid.uuid4().hex,'name':'Boosh','schema_version':1,'ingest_paths':['media']})
 conversion_done=staging/'conversion-complete.json';converter=None;log=None;backend=None
 try:
  if not conversion_done.exists():
   # Closed segments survive interruption. Preserve the final possibly-open
   # segment separately and reconvert it from its exact source offset.
   pending=sorted(staging.glob('part-*.mp4'))
   for part in pending[:-1]:
    i=int(part.stem.split('-')[1]);target=media/f'Boosh-{i+1:03d}-{i*5:03d}m.mp4'
    if not target.exists():os.replace(part,target)
   if pending:
    quarantine=staging/'interrupted';quarantine.mkdir(exist_ok=True)
    os.replace(pending[-1],quarantine/(uuid.uuid4().hex+'-'+pending[-1].name))
   first=next((i for i in range(status['total']) if not (media/f'Boosh-{i+1:03d}-{i*5:03d}m.mp4').exists()),status['total'])
   if first<status['total']:
    log=(staging/'conversion.log').open('a')
    command=[str(ROOT/'bin/ffmpeg'),'-nostdin','-hide_banner','-loglevel','warning','-ss',str(first*300),'-i',str(source),'-map','0:v:0','-map','0:a:0','-vf','scale=1280:-2','-c:v','h264_videotoolbox','-b:v','4000k','-force_key_frames','expr:gte(t,n_forced*300)','-c:a','copy','-f','segment','-segment_time','300','-segment_start_number',str(first),'-reset_timestamps','1','-segment_format_options','movflags=+faststart','-progress',str(staging/'conversion-progress.txt'),str(staging/'part-%04d.mp4')]
    converter=subprocess.Popen(command,stdout=log,stderr=log)
  options={'interval':2,'max_frames':12,'timeout':1800}
  update('warming_models',conversion_pid=converter.pid if converter else None)
  backend=SearchBackend(ROOT,lambda e:None)
  if (notes/'catalog.json').exists():
   update('publishing_completed_parts');publish_index(project,backend)
  with Engine(models_root=ROOT/'models',**options) as engine:
   engine.prewarm()
   for i in range(status['total']):
    part=staging/f'part-{i:04d}.mp4';target=media/f'Boosh-{i+1:03d}-{i*5:03d}m.mp4'
    while not target.exists():
     finished=converter is None or converter.poll() is not None
     if converter and finished and converter.returncode!=0:raise RuntimeError('Conversion failed; inspect preparation/conversion.log')
     closed=part.exists() and (finished or (staging/f'part-{i+1:04d}.mp4').exists())
     if closed:os.replace(part,target);break
     if finished:raise RuntimeError(f'Missing converted part {i}')
     update('converting',part=i+1);time.sleep(3)
    update('indexing',part=i+1,part_start_seconds=i*300)
    result=process(target,project,models_root=ROOT/'models',engine=engine,options=options,
                   progress_event=lambda e:update('indexing',part=i+1,analysis=e))
    if result['counts']['failed']:raise RuntimeError(f'AI analysis failed on part {i+1}; inspect catalog')
    status['parts'].append({'path':str(target.relative_to(project)),'source_start_seconds':i*300,'counts':result['counts']})
    update('part_complete',completed=i+1)
    update('publishing_completed_parts',completed=i+1)
    index=publish_index(project,backend)
    update('search_ready',index=index,completed=i+1)
   if converter:
    converter.wait()
    if converter.returncode:raise RuntimeError('Conversion failed')
   atomic_json(conversion_done,{'source':str(source),'source_stat':{'size':source.stat().st_size,'mtime_ns':source.stat().st_mtime_ns},'parts':status['parts']})
  update('building_search_index')
  index=publish_index(project,backend)
  update('complete',index=index,wallclock_ratio=(time.time()-started)/duration)
 except BaseException as error:
  update('interrupted' if isinstance(error,KeyboardInterrupt) else 'error',error=f'{type(error).__name__}: {error}')
  raise
 finally:
  if converter and converter.poll() is None:converter.terminate();converter.wait()
  if backend:backend.close()
  if log:log.close()

if __name__=='__main__':main()
