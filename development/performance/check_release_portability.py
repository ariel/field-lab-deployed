"""CPU-only staged release portability inventory. Does not infer models."""
from pathlib import Path
import os,json,time,subprocess
ROOT=Path('/Volumes/ThunderBlade X8/AI Indexer Lab');release=(ROOT/'release').resolve();outside=[];links=0
for folder,dirs,files in os.walk(release,followlinks=False):
 for name in dirs+files:
  p=Path(folder)/name
  if p.is_symlink():
   links+=1
   if not p.resolve().is_relative_to(release):outside.append({'path':str(p.relative_to(release)),'target':os.readlink(p)})
refs=[]
for rel in ['ditnotes','dit_notes.py','ingest_service.py','setup_workflow.py']:
 p=release/rel;files=p.rglob('*.py') if p.is_dir() else [p]
 for f in files:
  text=f.read_text()
  if any(t in text for t in ['DITNotesPrototype','AI Indexer Lab','lab_indexer']):refs.append(str(f.relative_to(release)))
commands={'python_imports':[str(release/'.venv/bin/python'),'-c','import sys,cv2,mlx,mlx_audio,mlx_vlm; print(sys.version); print("cv2",cv2.__version__)'],'node':[str(release/'bin/node'),'--version'],'ffmpeg':[str(release/'bin/ffmpeg'),'-version']};results={}
for name,args in commands.items():
 r=subprocess.run(args,text=True,capture_output=True,timeout=30);results[name]={'passed':r.returncode==0,'stdout':r.stdout.splitlines()[:2],'stderr':r.stderr[:500]}
payload={'checked_at':time.time(),'release':str(release),'passed':not outside and not refs and all(x['passed'] for x in results.values()),'symlinks_checked':links,'external_symlinks':outside,'external_development_references':refs,'commands':results};(ROOT/'benchmarks/release-portability.json').write_text(json.dumps(payload,indent=2));print(json.dumps(payload,indent=2))
