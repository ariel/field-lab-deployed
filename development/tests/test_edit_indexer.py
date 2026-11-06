import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lab_indexer.project_store import ProjectStore
from lab_indexer.edit_indexer import EditIndexer
class IndexerTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'projects').mkdir(exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'projects',prefix='index-smoke-');self.project=Path(self.tmp.name);self.db=self.project/'_LAB_NOTES/project.sqlite3'
        with ProjectStore(self.db) as s:s.add_annotation('clip','First note')
    def tearDown(self):self.tmp.cleanup()
    def test_revision_gap_survives_failure_and_restart(self):
        def fail(_):raise RuntimeError('Interrupted fake index')
        worker=EditIndexer(self.project,runner=fail,verify=lambda _:1)
        with self.assertRaises(RuntimeError):worker.index_once()
        with ProjectStore(self.db) as s:self.assertEqual(s.indexed_edit_revision,-1)
        calls=[]
        def run(_):calls.append(1);return {'complete':True}
        worker=EditIndexer(self.project,runner=run,verify=lambda _:1)
        self.assertTrue(worker.index_once());self.assertFalse(worker.index_once());self.assertEqual(len(calls),1)
        with ProjectStore(self.db) as s:self.assertEqual(s.indexed_edit_revision,1)
    def test_edits_during_index_remain_pending(self):
        def run(_):
            with ProjectStore(self.db) as s:s.add_annotation('clip','Edit during indexing')
            return {'complete':True}
        worker=EditIndexer(self.project,runner=run,verify=lambda _:1);worker.index_once()
        self.assertTrue(worker.status['pending'])
        with ProjectStore(self.db) as s:self.assertEqual(s.edit_revision,2);self.assertEqual(s.indexed_edit_revision,1)
    def test_unverified_snapshot_does_not_advance(self):
        def verify(_):raise RuntimeError('No sealed snapshot')
        worker=EditIndexer(self.project,runner=lambda _:{'complete':True},verify=verify)
        with self.assertRaises(RuntimeError):worker.index_once()
        with ProjectStore(self.db) as s:self.assertEqual(s.indexed_edit_revision,-1)
if __name__=='__main__':unittest.main()
