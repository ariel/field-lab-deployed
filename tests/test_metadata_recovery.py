"""Canonical metadata recovery regression; CPU-only, no production data writes."""
import sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ditnotes.metadata_api import MetadataAPI
from ditnotes.project_store import ProjectStore
class Recovery(unittest.TestCase):
 def test_external_publication_clears_error(self):
  with tempfile.TemporaryDirectory() as d:
   project=Path(d);path=project/'_DIT_NOTES/project.sqlite3'
   with ProjectStore(path,project_id='test') as s:s.add_annotation('clip','Note');rev=s.edit_revision
   api=MetadataAPI.__new__(MetadataAPI);api.server=NS(project=project,catalog=NS(read=lambda:{'project':{'id':'test'},'assets':[{'id':'clip'}]}));api.error='Earlier failure'
   self.assertIsNotNone(api.state()['index_error'])
   with ProjectStore(path,project_id='test') as s:s.mark_indexed(rev)
   state=api.state();self.assertEqual(state['edit_revision'],state['indexed_edit_revision']);self.assertIsNone(state['index_error'])
 def test_idle_worker_clears_error(self):
  with tempfile.TemporaryDirectory() as d:
   project=Path(d)
   with ProjectStore(project/'_DIT_NOTES/project.sqlite3',project_id='test') as s:s.mark_indexed(s.edit_revision)
   api=MetadataAPI.__new__(MetadataAPI);api.server=NS(project=project,catalog=NS(read=lambda:{'project':{'id':'test'}}));api.error='Old error'
   class Stop:
    calls=0
    def is_set(self):self.calls+=1;return self.calls>2
    def wait(self,*a):return False
   api.stop=Stop();api.changed=NS(wait=lambda *_:None,clear=lambda:None);api._loop();self.assertIsNone(api.error)
if __name__=='__main__':unittest.main()
