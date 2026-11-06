"""Read-only UI bridge. Durable daemon queue/catalog remain authoritative."""
import threading,time,subprocess
class ProgressState:
 def __init__(self):
  self.lock=threading.RLock();self.value={'protocol_version':1,'stage':'idle','current':None,'total':None,'completed':0,'failed':0,'started_at':None,'updated_at':time.time(),'elapsed':0}
 def begin(self,current=None):
  with self.lock:self.value.update(stage='scanning',current=current,total=None,completed=0,failed=0,started_at=time.time(),updated_at=time.time(),elapsed=0)
 def update(self,**values):
  with self.lock:
   if not set(values)<=set(self.value):raise ValueError('Unknown progress field')
   for key in ('total','completed','failed'):
    if key in values and values[key] is not None and (not isinstance(values[key],int) or values[key]<0):raise ValueError('Invalid file count')
   combined=dict(self.value,**values)
   if combined['total'] is not None and combined['completed']+combined['failed']>combined['total']:raise ValueError('File counts exceed discovered total')
   self.value.update(values);self.value['updated_at']=time.time()
   if self.value['started_at']:self.value['elapsed']=max(0,time.time()-self.value['started_at'])
 def snapshot(self):
  with self.lock:
   result=dict(self.value)
   if result['started_at'] and result['stage'] not in ('complete','failed','idle'):result['elapsed']=max(0,time.time()-result['started_at'])
   return result

def open_progress(root,port=8766,*,ingest_root=None):
 bundle=root/'native-progress/dist/IndexerProgress.app'
 if not bundle.is_dir():return False
 try:
  subprocess.Popen(['/usr/bin/open','-a',str(bundle),'--args','--status-url',f'http://127.0.0.1:{int(port)}/api/status','--library-url',f'http://127.0.0.1:{int(port)}/','--ingests-path',str(ingest_root or root.parent/'Ingests')],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True,start_new_session=True)
  return True
 except OSError:return False
