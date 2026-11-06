"""Release A→B reanalysis and presentation-only upgrade tests without inference."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ditnotes import library
from ditnotes.project_store import ProjectStore

class FakeEngine:
    def __init__(self, revision, interrupt_after=None): self.revision=revision;self.interrupt_after=interrupt_after;self.calls=[]
    def analyze(self, source, output):
        if self.interrupt_after is not None and len(self.calls)>=self.interrupt_after:
            (output/'partial.json').write_text('{"not_published":true}')
            raise KeyboardInterrupt('simulated abrupt session interruption')
        self.calls.append(source.name)
        (output/'frame.jpg').write_bytes(b'fixture frame '+self.revision.encode())
        (output/'result.json').write_text(json.dumps({'status':'complete','duration':2,'probe':{'streams':[{'codec_type':'video','width':32,'height':32}]},'highlights':[{'seconds':1,'label':'Caption '+self.revision,'frame':'frame.jpg'}],'tracks':[],'timing':{'total_seconds':.01}}))

class UpgradeProfiles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name).resolve()
        self.release=self.base/'release';self.release.mkdir()
        for rel in ('ditnotes/audio_context.py','ditnotes/diarization.py','ditnotes/models.py','ditnotes/faces.py','ditnotes/face_models.py','ditnotes/engine.py','ditnotes/prompts/field-caption.txt','ditnotes/native/feature_select','ditnotes/native/feature_select.swift','viewer/src/main.jsx'):
            path=self.release/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture '+rel+' A\n')
        self.models=self.base/'model-generations/first';self.models.mkdir(parents=True)
        rows=[]
        for relative in ('parakeet/model.safetensors','parakeet/config.json','Qwen3.5-4B-4bit/model.safetensors','diarization/model.safetensors','speaker/model.safetensors','faces/sface.onnx','mlx-search/text/model.safetensors','.runtime/browser/ort.wasm'):
            path=self.models/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(('fixture '+relative).encode())
            rows.append({'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
        self.lock={'model_files':rows,'model_json':{'model-lock.json':{'speaker':'pin-A'},'faces/manifest.json':{'model':'sface-A'},'mlx-search/clip/manifest.json':{'model':'clip-A'}},'node':{'version':'A'}}
        (self.release/'deploy').mkdir();self.save_lock()
        self.patch=patch.object(library,'ROOT',self.release);self.patch.start();self.addCleanup(self.patch.stop)
    def save_lock(self): (self.release/'deploy/assets.lock.json').write_text(json.dumps(self.lock))
    def profile(self, models=None, **options): return library.profile_id(models or self.models,options)
    def test_caption_prompt_and_engine_changes_invalidate_analysis(self):
        first=self.profile();prompt=self.release/'ditnotes/prompts/field-caption.txt'
        prompt.write_text('A shorter, changed visual description prompt\n');second=self.profile()
        self.assertNotEqual(first,second)
        engine=self.release/'ditnotes/engine.py';engine.write_text('SYSTEM = "changed inference instruction"\n')
        self.assertNotEqual(second,self.profile())
    def test_ui_browser_search_and_node_changes_preserve_analysis(self):
        first=self.profile();(self.release/'viewer/src/main.jsx').write_text('new React presentation')
        self.lock['node']['version']='B'
        for row in self.lock['model_files']:
            if row['path'].startswith(('mlx-search/','.runtime/')):row['sha256']='f'*64
        self.lock['model_json']['mlx-search/clip/manifest.json']['model']='clip-B';self.save_lock()
        self.assertEqual(first,self.profile())
    def test_relocated_identical_models_with_new_mtimes_reuse_profile(self):
        first=self.profile();second=self.base/'model-generations/second';shutil.copytree(self.models,second)
        for path in second.rglob('*'):
            if path.is_file():os.utime(path,ns=(1700000000000000000,1700000000000000000))
        self.assertEqual(first,self.profile(second))
    def test_all_analysis_model_pins_and_manifest_changes_invalidate(self):
        first=self.profile()
        for prefix in ('parakeet/','Qwen3.5-4B-4bit/','diarization/','speaker/','faces/'):
            row=next(r for r in self.lock['model_files'] if r['path'].startswith(prefix));old=row['sha256'];row['sha256']='f'*64;self.save_lock()
            self.assertNotEqual(first,self.profile(),prefix);row['sha256']=old
        self.lock['model_json']['model-lock.json']['speaker']='pin-B';self.save_lock();self.assertNotEqual(first,self.profile())
    def test_sampling_changes_invalidate_but_equivalent_defaults_do_not(self):
        self.assertEqual(self.profile(),self.profile(interval=2.0,max_frames=12.0,timeout=300.0,vision_width=960))
        self.assertNotEqual(self.profile(),self.profile(max_frames=16))
    def test_interrupted_upgrade_reuses_completed_new_profile_and_keeps_operator_edits(self):
        project=self.base/'production';scope=project/'20261105/A-CAM-001';scope.mkdir(parents=True)
        for i in range(3):(scope/f'clip-{i}.mp4').write_bytes(f'original media {i}'.encode())
        original_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scope.iterdir()}
        a=FakeEngine('A');result=library.process(scope,project,models_root=self.models,engine=a)
        self.assertEqual(result['counts'],{'files':3,'processed':3,'reused':0,'failed':0})
        notes=project/'_DIT_NOTES';identity=json.loads((notes/'project.json').read_text());old_catalog=json.loads((notes/'catalog.json').read_text())
        content=old_catalog['assets'][0]['content_id'];asset_ids=[x['id'] for x in old_catalog['assets']]
        with ProjectStore(notes/'project.sqlite3',project_id=identity['id']) as store:
            store.add_annotation(content,'Operator field note',metadata={'tags':['keep this'],'location':'field'})
            face=store.assign_face(content,1,None,'fixture-face',.9,bbox=[.1,.1,.5,.5])['face_id'];store.name_face(face,'Ariel')
            voice=store.provisional_speaker(content,'fixture-speaker',0,2)['person_id'];store.link_face_voice(face,voice,'operator reviewed')
            saved_annotations=store.annotations();saved_faces=store.faces();saved_people=store.people();saved_revision=store.edit_revision
        old_profile=self.profile();(self.release/'ditnotes/prompts/field-caption.txt').write_text('Prompt B\n');new_profile=self.profile();self.assertNotEqual(old_profile,new_profile)
        interrupted=FakeEngine('B',interrupt_after=1)
        with self.assertRaises(KeyboardInterrupt):library.process(scope,project,models_root=self.models,engine=interrupted)
        self.assertEqual(interrupted.calls,['clip-0.mp4'])
        state=library.reconcile(project,input_paths=[scope],models_root=self.models)
        self.assertEqual(state['counts'],{'files':3,'ready':1,'pending':2})
        resumed=FakeEngine('B');result=library.process(scope,project,models_root=self.models,engine=resumed)
        self.assertEqual(result['counts'],{'files':3,'processed':2,'reused':1,'failed':0});self.assertEqual(resumed.calls,['clip-1.mp4','clip-2.mp4'])
        new_catalog=json.loads((notes/'catalog.json').read_text())
        self.assertEqual([x['id'] for x in new_catalog['assets']],asset_ids)
        self.assertTrue(all(x['highlights'][0]['note']=='Caption B' for x in new_catalog['assets']))
        self.assertEqual(json.loads((notes/'project.json').read_text())['id'],identity['id'])
        self.assertEqual(len(list((notes/'.objects').glob('*/*/complete.json'))),6)
        with ProjectStore(notes/'project.sqlite3',project_id=identity['id']) as store:
            self.assertEqual(store.annotations(),saved_annotations);self.assertEqual(store.faces(),saved_faces);self.assertEqual(store.people(),saved_people);self.assertEqual(store.edit_revision,saved_revision)
        (self.release/'viewer/src/main.jsx').write_text('React UI B\n')
        ui_only=FakeEngine('should never execute');result=library.process(scope,project,models_root=self.models,engine=ui_only)
        self.assertEqual(result['counts'],{'files':3,'processed':0,'reused':3,'failed':0});self.assertEqual(ui_only.calls,[])
        self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scope.iterdir()},original_hashes)

    def test_ui_refresh_reindexes_search_without_constructing_inference_engine(self):
        project=self.base/'ui-project';project.mkdir();(project/'clip.mp4').write_bytes(b'original test media')
        library.process(project/'clip.mp4',project,models_root=self.models,engine=FakeEngine('A'))
        spec=importlib.util.spec_from_file_location('test_reindex_module',ROOT/'deploy/reindex.py');reindex=importlib.util.module_from_spec(spec);spec.loader.exec_module(reindex)
        (self.release/'viewer/src/main.jsx').write_text('React UI change only')
        class Backend:
            def __init__(self,*args,**kwargs):pass
            def close(self):pass
        with patch.object(reindex,'ROOT',self.release),patch('ditnotes.engine.Engine',side_effect=AssertionError('Inference must not load')),patch('ditnotes.search_backend.SearchBackend',Backend),patch('ditnotes.enrichment.publish_index',return_value={'published':True}) as publish:
            plan=reindex.plan(project);self.assertEqual(plan['analyze'],0);self.assertEqual(plan['reuse'],1)
            result=reindex.execute(project)
            self.assertEqual(result['counts'],{'processed':0,'reused':1,'failed':0,'files':1});self.assertEqual(result['remaining'],0)
            publish.assert_called_once();self.assertTrue(Path(result['operator_backup']).is_file())

if __name__=='__main__':unittest.main()
