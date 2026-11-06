from pathlib import Path
import json,time,sqlite3
ROOT=Path('/Volumes/ThunderBlade X8/AI Indexer');LAB=Path('/Volumes/ThunderBlade X8/AI Indexer Lab');events=[];last=None;seen=False;deadline=time.time()+1200
while time.time()<deadline:
 try:
  status=json.loads((ROOT/'runtime/status.json').read_text());key=(status.get('phase'),status.get('active'),status.get('stage'),status.get('current'),status.get('pending'),status.get('errors'))
  if key!=last:
   events.append({'observed_at':time.time(),'status':status});last=key;(LAB/'benchmarks/canonical-timeline.json').write_text(json.dumps(events,indent=2));print(json.dumps({'at':time.time(),'state':key}),flush=True)
  if status.get('pending',0)>0 or status.get('phase') in ['processing','warming']:seen=True
  if status.get('phase')=='error':break
  if seen and status.get('phase')=='ready' and status.get('pending')==0:break
 except (OSError,ValueError):pass
 time.sleep(3)
print('WATCH_DONE',flush=True)
