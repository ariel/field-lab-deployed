"""OffShoot setup contract tests: disposable homes and mocked app settings only."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import setup_workflow as setup


class OffShootSetup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / "Field Lab — Ariel's laptop"; self.home.mkdir()
        self.user = self.base / 'user'; self.user.mkdir()
        self.release = self.home / 'releases/test-release'; self.release.mkdir(parents=True)
        (self.home / 'current').symlink_to(self.release)
        (self.home / 'shared/runtime').mkdir(parents=True)
        (self.release / 'runtime').symlink_to(self.home / 'shared/runtime')
        (self.release / 'offshoot').mkdir()
        shutil.copy2(ROOT / 'offshoot/Verified Ingest.hedge', self.release / 'offshoot/Verified Ingest.hedge')
        self.app = self.base / 'OffShoot.app'; (self.app / 'Contents').mkdir(parents=True)
        with (self.app / 'Contents/Info.plist').open('wb') as f:
            plistlib.dump({'CFBundleShortVersionString': '26.3.1', 'CFBundleIdentifier': 'test.offshoot'}, f)
        self.volume = self.base / 'Production Drive'; self.volume.mkdir()
        self.project = self.volume / 'Trip media/Offloads'; self.project.mkdir(parents=True)
        (self.project / '20261105/CAM-150').mkdir(parents=True)
        self.config = {'volume_mount': str(self.volume), 'ingest_root': str(self.project), 'ingest_folder': 'Trip media/Offloads', 'volume_uuid': 'TEST-UUID', 'port': 8766}
        self.preset = self.user / 'Library/Preferences/Hedge/Presets/Verified Ingest.hedge'
        self.preset.parent.mkdir(parents=True)
        self.preset.write_text('[{"counter":"199","folderPattern":"old"}]')
        self.export = plistlib.dumps({'SFIDefaultsDestinationDirectoryFormatIncrementer': '200', 'keep': 'original setting'})

    @contextlib.contextmanager
    def mocked_main(self, export_ok=True, api_failure=False, extra_args=()):
        home, app = self.user, self.app
        original_path = Path
        class TestPath(type(Path())):
            def __new__(cls, *parts):
                if len(parts) == 1 and str(parts[0]) == '/Applications/OffShoot.app': parts = (app,)
                return super().__new__(cls, *parts)
            def __init__(self, *parts):
                if len(parts) == 1 and str(parts[0]) == '/Applications/OffShoot.app': parts = (app,)
                super().__init__(*parts)
            @classmethod
            def home(cls): return cls(home)
        def command(args, **kwargs):
            if list(map(str, args[:3])) == ['/usr/bin/defaults', 'export', 'test.offshoot']:
                return subprocess.CompletedProcess(args, 0 if export_ok else 1, stdout=self.export, stderr=b'')
            if 'prepare-offline' in args:
                return subprocess.CompletedProcess(args, 0, stdout='{"ready":true}', stderr='')
            raise AssertionError('Unexpected external command: ' + repr(args))
        with patch.object(setup, 'ROOT', self.release), patch.object(setup, 'Path', TestPath), \
             patch.object(setup, 'config', return_value=self.config), patch.object(setup, 'verify_volume') as volume, \
             patch.object(setup.platform, 'machine', return_value='arm64'), \
             patch.object(setup.subprocess, 'check_output', return_value='27.0\n'), \
             patch.object(setup.subprocess, 'run', side_effect=command), \
             patch.object(setup, 'compile_hooks', return_value={'OffShoot Started': str(self.home / 'shared/runtime/offshoot-hooks/OffShoot Started.scpt'), 'File Copy Completed': str(self.home / 'shared/runtime/offshoot-hooks/File Copy Completed.scpt')}) as hooks, \
             patch.object(setup, 'api', side_effect=RuntimeError('test vendor rejection') if api_failure else None) as api, \
             patch.object(setup, 'start') as start, \
             patch.object(sys, 'argv', ['setup_workflow.py', '--home', str(self.home), *extra_args]), \
             contextlib.redirect_stdout(io.StringIO()):
            yield api, hooks, start

    def test_backup_failure_changes_no_preferences_or_hooks(self):
        before = self.preset.read_bytes()
        with self.mocked_main(export_ok=False, extra_args=['--offshoot-idle']) as (api, hooks, start):
            with self.assertRaisesRegex(RuntimeError, 'Cannot back up'): setup.main()
            api.assert_not_called(); hooks.assert_not_called(); start.assert_not_called()
        self.assertEqual(self.preset.read_bytes(), before)
        self.assertFalse((self.release / 'runtime/setup-receipt.json').exists())

    def test_counter_and_custom_folder_preserved_backups_written(self):
        before = self.preset.read_bytes()
        with self.mocked_main(extra_args=['--offshoot-idle']) as (api, hooks, start):
            setup.main(); start.assert_not_called(); hooks.assert_called_once()
            self.assertEqual(api.call_args_list[-1].args, ('setDestination',))
            self.assertEqual(api.call_args_list[-1].kwargs['path'], str(self.volume))
        preset = json.loads(self.preset.read_text())[0]
        self.assertEqual(preset['counter'], '200')
        self.assertEqual(preset['folderPattern'], 'Trip media/Offloads/{YYYY}{MM}{DD}/{Source Name}-{Counter}')
        receipt = json.loads((self.release / 'runtime/setup-receipt.json').read_text())
        self.assertFalse(receipt['ccc_configured']); self.assertEqual(receipt['counter'], '200')
        backups = list((self.release / 'runtime/setup-backups').iterdir()); self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / self.preset.name).read_bytes(), before)
        self.assertEqual((backups[0] / 'offshoot-preferences.plist').read_bytes(), self.export)
        self.assertEqual(json.loads((backups[0] / 'plan.json').read_text())['counter'], '200')

    def test_filesystem_counter_can_advance_saved_counter(self):
        (self.project / '20261105/B-CAM-215').mkdir()
        with self.mocked_main(extra_args=['--offshoot-idle']): setup.main()
        self.assertEqual(json.loads(self.preset.read_text())[0]['counter'], '216')

    def test_idle_confirmation_required_before_app_commands(self):
        with self.mocked_main() as (api, hooks, start):
            with self.assertRaisesRegex(RuntimeError, 'active or queued'): setup.main()
            api.assert_not_called(); hooks.assert_not_called(); start.assert_not_called()

    def test_partial_vendor_failure_explicit_and_durable(self):
        with self.mocked_main(api_failure=True, extra_args=['--offshoot-idle']) as (_, _, start):
            with self.assertRaisesRegex(RuntimeError, 'partially applied'): setup.main()
            start.assert_not_called()
        backup = next((self.release / 'runtime/setup-backups').iterdir())
        self.assertTrue(json.loads((backup / 'failure.json').read_text())['partial_configuration_possible'])
        self.assertFalse((self.release / 'runtime/setup-receipt.json').exists())

    def test_api_waits_for_empty_ack_then_success_and_url_encodes(self):
        log = self.user / 'Library/Logs/Hedge/urlSchemeResponseLog.txt'
        log.parent.mkdir(parents=True)
        log.write_text('stale previous response')
        def open_url(command, **kwargs):
            self.assertEqual(command[0], '/usr/bin/open')
            self.assertIn('path=%2FVolumes%2FA%20%26%20B', command[1])
            log.write_text('')
            return subprocess.CompletedProcess(command, 0)
        def finish_ack(_): log.write_text('success')
        with patch.object(setup.Path, 'home', return_value=self.user), patch.object(setup.subprocess, 'run', side_effect=open_url) as run, patch.object(setup.time, 'sleep', side_effect=finish_ack) as sleep:
            setup.api('setDestination', path='/Volumes/A & B')
        run.assert_called_once(); sleep.assert_called_once()

    @unittest.skipUnless(Path('/usr/bin/osacompile').is_file(), 'macOS compiler required')
    def test_real_hook_compile_unicode_spaces_and_shell_metacharacters(self):
        special = self.base / 'Ariel’s "field" lab $HOME `literal`'
        hooks = setup.compile_hooks(special)
        self.assertEqual(set(hooks), {'OffShoot Started', 'File Copy Completed'})
        for name, path in hooks.items():
            self.assertTrue(Path(path).is_file()); self.assertGreater(Path(path).stat().st_size, 0)
            source = Path(path).with_suffix('.applescript').read_text()
            self.assertIn(str(special / 'run').replace('"', '\\"'), source)
            self.assertNotIn('/releases/', source); self.assertNotIn(str(ROOT), source)
            # Decompile only: callbacks are never run, and no app is opened.
            decompiled = subprocess.check_output(['/usr/bin/osadecompile', path], text=True)
            self.assertIn('do shell script', decompiled)

if __name__ == '__main__': unittest.main()
