"""Destructive failure cases run only in disposable temporary directories."""
import fcntl
import errno
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('deployment_manager', Path(__file__).resolve().parents[1] / 'deploy/manager.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.source = self.root / 'checkout'; self.source.mkdir()
        (self.source / 'dit_notes.py').write_text('print("prototype")\n')
        (self.source / 'config.json').write_text('{"volume_uuid":"DO NOT COPY"}')
        (self.source / 'deploy').mkdir(); (self.source / 'deploy/assets.lock.json').write_text('{"schema":1}')
        self.home = self.root / 'Application Support/Field Lab'
        self.addCleanup(patch.stopall)
        patch.object(m, 'offline_check', return_value={'ready': True}).start()

    def activate(self, *args, **kwargs):
        return m.activate(*args, **kwargs, checker=lambda _: {'ready': True})

    def candidate(self, text=None):
        if text: (self.source / 'dit_notes.py').write_text(text)
        info = m.stage(self.source, self.home); release = Path(info['release'])
        (release / '.venv').mkdir(exist_ok=True)
        (release / '.venv/pyvenv.cfg').write_text('version = 3.12.16\n')
        (release / 'viewer/dist').mkdir(parents=True, exist_ok=True)
        (release / 'viewer/dist/index.html').write_text('<html></html>')
        m.atomic_json(release / 'deploy-ready.json', {'ready': True, 'release_id': info['release_id'], 'generated_files': {p: m.digest(release / p) for p in ('.venv/pyvenv.cfg', 'viewer/dist/index.html')}})
        m.mark_ready(self.home, info['release_id'], checker=lambda _: {'ready': True})
        return info

    def test_separate_shared_state_and_no_host_config(self):
        info = m.stage(self.source, self.home); release = Path(info['release'])
        self.assertTrue((release / 'config.json').is_symlink())
        self.assertFalse((self.home / 'shared/config.json').exists())
        self.assertEqual((release / 'runtime').resolve(), (self.home / 'shared/runtime').resolve())

    def test_update_and_rollback_preserve_state(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        durable = self.home / 'shared/runtime/queue.sqlite3'; durable.write_bytes(b'queue sentinel')
        config = self.home / 'shared/config.json'; config.write_text('{"local":true}')
        second = self.candidate('print("second")\n'); self.activate(self.home, second['release_id'])
        self.assertEqual((self.home / 'current').resolve().name, second['release_id'])
        self.activate(self.home, rollback=True)
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])
        self.assertEqual(durable.read_bytes(), b'queue sentinel'); self.assertEqual(config.read_text(), '{"local":true}')

    def test_interrupted_staging_keeps_current_and_retries(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        (self.source / 'dit_notes.py').write_text('changed\n')
        def die(*_): raise RuntimeError('simulated power loss')
        with self.assertRaises(RuntimeError): m.stage(self.source, self.home, fault=die)
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])
        self.assertEqual(len(m.status(self.home)['staging']), 1)
        next_release = m.stage(self.source, self.home)
        self.assertNotEqual(next_release['release_id'], first['release_id'])

    def test_failed_bootstrap_never_switches(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        (self.source / 'dit_notes.py').write_text('next\n'); candidate = m.stage(self.source, self.home)
        with self.assertRaises(FileNotFoundError): self.activate(self.home, candidate['release_id'])
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])

    def test_model_readiness_failure_does_not_mark_ready(self):
        info = self.candidate(); release = Path(info['release']); (release / '.field-lab-ready.json').unlink()
        with self.assertRaises(RuntimeError): m.mark_ready(self.home, info['release_id'], checker=lambda _: {'ready': False})
        self.assertFalse((release / '.field-lab-ready.json').exists())

    def test_source_and_generated_tamper_fail_closed(self):
        info = self.candidate(); release = Path(info['release'])
        (release / 'viewer/dist/index.html').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'Generated asset seal'): self.activate(self.home, info['release_id'])
        (release / 'dit_notes.py').write_text('tampered source')
        with self.assertRaisesRegex(ValueError, 'Source seal'): self.activate(self.home, info['release_id'])

    def test_manifest_tamper_fails_closed(self):
        info = self.candidate(); release = Path(info['release'])
        data = json.loads((release / '.field-lab-release.json').read_text())
        data['files']['dit_notes.py']['sha256'] = '0' * 64; m.atomic_json(release / '.field-lab-release.json', data)
        with self.assertRaisesRegex(ValueError, 'identity mismatch'): self.activate(self.home, info['release_id'])

    def test_source_symlink_rejected(self):
        (self.source / 'leak').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError, 'regular file'): m.stage(self.source, self.home)

    def test_shared_symlink_rejected(self):
        m.layout(self.home); (self.home / 'shared/model-generations').rmdir()
        (self.home / 'shared/model-generations').symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, 'symlink directory'): m.stage(self.source, self.home)

    def test_escaping_manifest_path_rejected(self):
        info = self.candidate(); release = Path(info['release'])
        data = json.loads((release / 'deploy-ready.json').read_text()); data['generated_files']['../elsewhere'] = '0' * 64
        m.atomic_json(release / 'deploy-ready.json', data)
        with self.assertRaisesRegex(ValueError, 'Invalid manifest path'): self.activate(self.home, info['release_id'])

    def test_concurrent_update_lock(self):
        with m.locked(self.home):
            with self.assertRaisesRegex(RuntimeError, 'Another deployment'): m.stage(self.source, self.home)

    def test_running_service_blocks_switch(self):
        info = self.candidate()
        with (self.home / 'shared/runtime/service.lock').open('a+') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, 'service is running'): self.activate(self.home, info['release_id'])
        self.assertFalse((self.home / 'current').exists())

    def test_switch_crash_is_old_or_new_complete_release(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        second = self.candidate('new\n')
        def before(point, _):
            if point == 'before-switch': raise RuntimeError('cut power')
        with self.assertRaises(RuntimeError): self.activate(self.home, second['release_id'], fault=before)
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])
        def after(point, _):
            if point == 'after-switch': raise RuntimeError('cut power')
        with self.assertRaises(RuntimeError): self.activate(self.home, second['release_id'], fault=after)
        self.assertEqual((self.home / 'current').resolve().name, second['release_id'])
        self.activate(self.home, rollback=True)
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])

    def test_no_source_home_overlap(self):
        with self.assertRaisesRegex(ValueError, 'separate'): m.stage(self.source, self.source / 'deployed')

    def test_extra_importable_code_rejected(self):
        info = self.candidate(); release = Path(info['release'])
        (release / 'sitecustomize.py').write_text('raise RuntimeError("injected")')
        with self.assertRaisesRegex(ValueError, 'unsealed'): self.activate(self.home, info['release_id'])

    def test_extra_dependency_module_rejected(self):
        info = self.candidate(); release = Path(info['release'])
        (release / '.venv/injected.py').write_text('unexpected dependency module')
        with self.assertRaisesRegex(ValueError, 'inventory changed'): self.activate(self.home, info['release_id'])

    def test_generated_internal_symlink_allowed_external_rejected(self):
        info = self.candidate(); release = Path(info['release'])
        (release / '.venv/config-link').symlink_to('pyvenv.cfg')
        receipt = json.loads((release / 'deploy-ready.json').read_text())
        receipt['generated_files']['.venv/config-link'] = m.digest(release / '.venv/config-link')
        m.atomic_json(release / 'deploy-ready.json', receipt)
        m.mark_ready(self.home, info['release_id'], checker=lambda _: {'ready': True})
        self.activate(self.home, info['release_id'])
        (release / '.venv/config-link').unlink()
        (release / '.venv/config-link').symlink_to(self.source / 'dit_notes.py')
        with self.assertRaisesRegex(ValueError, 'escaped'): self.activate(self.home, info['release_id'])

    def test_model_generation_change_isolated(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        old_models = Path(first['release']) / 'models'; (old_models / 'weight').write_bytes(b'old weights')
        (self.source / 'deploy/assets.lock.json').write_text('{"schema":2}')
        second = self.candidate('second\n'); new_models = Path(second['release']) / 'models'
        self.assertNotEqual(old_models.resolve(), new_models.resolve())
        (new_models / 'weight').write_bytes(b'new weights')
        self.assertEqual((old_models / 'weight').read_bytes(), b'old weights')
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])

    def test_activation_rechecks_current_offline_readiness(self):
        info = self.candidate()
        with self.assertRaisesRegex(RuntimeError, 'offline readiness'):
            m.activate(self.home, info['release_id'], checker=lambda _: {'ready': False})
        self.assertFalse((self.home / 'current').is_symlink())

    def test_real_sigkill_releases_lock_and_preserves_current(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        (self.source / 'dit_notes.py').write_text('new after kill\n')
        code = '''import importlib.util,os,signal,sys
spec=importlib.util.spec_from_file_location('manager',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def die(*args):os.kill(os.getpid(),signal.SIGKILL)
m.stage(sys.argv[2],sys.argv[3],fault=die)
'''
        result = subprocess.run([sys.executable, '-c', code, str(Path(m.__file__)), str(self.source), str(self.home)], capture_output=True)
        self.assertEqual(result.returncode, -9)
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])
        self.assertEqual(len(m.status(self.home)['staging']), 1)
        self.assertFalse(m.stage(self.source, self.home)['reused'])

    def test_out_of_space_preserves_active_release(self):
        first = self.candidate(); self.activate(self.home, first['release_id'])
        (self.source / 'dit_notes.py').write_text('new but no disk space\n')
        with patch.object(m.shutil, 'copyfile', side_effect=OSError(errno.ENOSPC, 'No space left')):
            with self.assertRaises(OSError): m.stage(self.source, self.home)
        self.assertEqual((self.home / 'current').resolve().name, first['release_id'])
        self.assertFalse(m.stage(self.source, self.home)['reused'])

    def test_git_provenance_is_optional_and_reported(self):
        info=self.candidate();manifest=json.loads((Path(info['release'])/'.field-lab-release.json').read_text())
        self.assertIsNone(manifest['git_commit']);self.assertIsNone(manifest['git_dirty'])
        self.activate(self.home,info['release_id'])
        self.assertEqual(m.status(self.home)['current_provenance'],{'release_id':info['release_id'],'git_commit':None,'git_dirty':None})

    def test_git_provenance_captures_clean_and_dirty_checkout(self):
        def git(*args):subprocess.run(['git','-C',str(self.source),*args],check=True,capture_output=True)
        git('init');git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Fixture')
        clean=m.git_provenance(self.source);self.assertEqual(len(clean['git_commit']),40);self.assertFalse(clean['git_dirty'])
        (self.source/'dit_notes.py').write_text('modified after commit\n')
        info=m.stage(self.source,self.home);manifest=json.loads((Path(info['release'])/'.field-lab-release.json').read_text())
        self.assertEqual(manifest['git_commit'],clean['git_commit']);self.assertTrue(manifest['git_dirty'])

if __name__ == '__main__': unittest.main()
