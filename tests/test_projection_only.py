"""Maintenance publication updates search without identity or annotation mutations."""
import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from ditnotes.project_store import ProjectStore
from ditnotes.enrichment import _publish

class ProjectionOnly(unittest.TestCase):
 def test_projection_only_skips_grouping_and_inheritance_but_indexes_saved_edits(self):
  with tempfile.TemporaryDirectory() as directory,patch('ditnotes.sqlite_safety.require_safe_sqlite'):
   project=Path(directory).resolve();notes=project/'_DIT_NOTES';notes.mkdir()
   (notes/'catalog.json').write_text(json.dumps({'project':{'id':'fixture'},'assets':[]}))
   with ProjectStore(notes/'project.sqlite3',project_id='fixture') as store:
    store.provisional_speaker('clip','speaker',0,3);store.add_annotation('clip','Keep operator note');revision=store.edit_revision
    before={table:[tuple(r) for r in store.db.execute('select * from '+table)] for table in ('people','observations','annotations','links')}
   backend=SimpleNamespace(readiness=lambda:{'ready':True,'revision':{}},_infer=None)
   with patch('ditnotes.identity_grouping.regroup',side_effect=AssertionError('Must not regroup voices')),patch('ditnotes.enrichment._links',side_effect=AssertionError('Must not inherit notes')),patch('ditnotes.enrichment.build',return_value={'vectors':[]}),patch('ditnotes.enrichment.read_snapshot',return_value={'catalog':{'search_projection':{'edit_revision':revision}}}):
    result=_publish(project,backend,projection_only=True)
   self.assertTrue(result['ready']);self.assertEqual(result['indexed_edit_revision'],revision)
   with ProjectStore(notes/'project.sqlite3') as store:
    for table,rows in before.items():self.assertEqual([tuple(r) for r in store.db.execute('select * from '+table)],rows)
if __name__=='__main__':unittest.main()
