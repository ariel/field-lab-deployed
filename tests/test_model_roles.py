"""Offline model role/completeness checks use tiny disposable fake safetensors."""
import json,tempfile,unittest
from pathlib import Path
import dit_notes
from ditnotes.model_roles import ANALYSIS_MODELS,CHAT_MODEL,FAST_VISION_MODEL,MODEL_LOCK,MODEL_ROLES,model_path


def weight(path):
    header=json.dumps({'fixture':{'dtype':'F32','shape':[1],'data_offsets':[0,4]}}).encode()
    path.write_bytes(len(header).to_bytes(8,'little')+header+b'\0'*4)


class ModelRoles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for name in MODEL_LOCK:
            folder=self.root/'models'/name;folder.mkdir(parents=True)
            for item in ['config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json']:(folder/item).write_text('{}')
            if name=='parakeet':(folder/'tokenizer.model').write_bytes(b'fixture')
            weight(folder/'model.safetensors')
    def test_model_roles_are_distinct_and_explicit(self):
        self.assertEqual(MODEL_ROLES,{'ingest_vision':FAST_VISION_MODEL,'agentic_chat':CHAT_MODEL})
        self.assertEqual(model_path(self.root,'agentic_chat'),self.root/'models/Qwen3.8-27B-4bit')
        self.assertNotIn(CHAT_MODEL,ANALYSIS_MODELS)
        with self.assertRaises(ValueError):model_path(self.root,'unknown')
    def test_all_roles_are_present_in_offline_inventory(self):
        self.assertEqual(set(dit_notes.model_readiness(self.root)),set(MODEL_LOCK))
        self.assertTrue(all(x['ready'] for x in dit_notes.model_readiness(self.root).values()))
    def test_missing_big_chat_weight_does_not_fall_back_to_fast_model(self):
        (self.root/'models'/CHAT_MODEL/'model.safetensors').unlink()
        state=dit_notes.model_readiness(self.root)
        self.assertFalse(state[CHAT_MODEL]['ready']);self.assertTrue(state[FAST_VISION_MODEL]['ready'])
        self.assertIn('model.safetensors missing/truncated',state[CHAT_MODEL]['errors'])
    def test_missing_or_truncated_chat_shard_is_not_ready(self):
        folder=self.root/'models'/CHAT_MODEL
        (folder/'model.safetensors').rename(folder/'part1.safetensors')
        (folder/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'a':'part1.safetensors','b':'part2.safetensors'}}))
        self.assertFalse(dit_notes.model_readiness(self.root)[CHAT_MODEL]['ready'])
        (folder/'part2.safetensors').write_bytes(b'truncated')
        self.assertFalse(dit_notes.model_readiness(self.root)[CHAT_MODEL]['ready'])
        weight(folder/'part2.safetensors')
        self.assertTrue(dit_notes.model_readiness(self.root)[CHAT_MODEL]['ready'])
    def test_chat_index_cannot_escape_model_directory(self):
        folder=self.root/'models'/CHAT_MODEL
        (folder/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'a':'../escape.safetensors'}}))
        self.assertFalse(dit_notes.model_readiness(self.root)[CHAT_MODEL]['ready'])
    def test_chat_lock_is_immutable_and_downloads_no_python_code(self):
        root=Path(__file__).resolve().parents[1];lock=json.loads((root/'deploy/assets.lock.json').read_text())
        rows=[row for row in lock['model_files'] if row['path'].startswith(CHAT_MODEL+'/')]
        self.assertEqual(len(rows),14);self.assertEqual(sum(row['bytes'] for row in rows),16081489363)
        for row in rows:
            self.assertEqual(len(row['sha256']),64)
            self.assertIn('/resolve/'+MODEL_LOCK[CHAT_MODEL][1]+'/',row['url'])
            self.assertFalse(row['path'].endswith('.py'))
        self.assertEqual(len([r for r in rows if r['path'].endswith('.safetensors')]),3)

if __name__=='__main__':unittest.main()
