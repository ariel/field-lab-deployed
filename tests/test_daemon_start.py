"""No mounted volumes/apps: a disposable child exercises the startup lock handoff."""
import fcntl,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import ingest_service

class StartupLock(unittest.TestCase):
 def test_start_waits_until_child_owns_service_lock(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'runtime').mkdir();child=None
   real_popen=subprocess.Popen
   def spawn(*args,**kwargs):
    nonlocal child
    code="import fcntl,time,sys; time.sleep(.25); f=open(sys.argv[1],'a+'); fcntl.flock(f,fcntl.LOCK_EX); time.sleep(10)"
    child=real_popen([sys.executable,'-c',code,str(root/'runtime/service.lock')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return child
   try:
    with patch.object(ingest_service,'ROOT',root),patch.object(ingest_service,'config',return_value={'port':18799,'ingest_root':folder}),patch.object(ingest_service,'verify_volume'),patch.object(ingest_service,'open_progress'),patch.object(ingest_service.subprocess,'Popen',side_effect=spawn):
     started=time.monotonic();result=ingest_service.start()
    self.assertGreater(time.monotonic()-started,.2);self.assertEqual(result['status'],'starting')
    with (root/'runtime/service.lock').open('a+') as f:
     with self.assertRaises(BlockingIOError):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   finally:
    if child:child.terminate();child.wait(timeout=5)
if __name__=='__main__':unittest.main()
