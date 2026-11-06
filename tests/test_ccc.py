import importlib.util
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('ccc_read_only',Path(__file__).resolve().parents[1]/'deploy/ccc.py')
ccc=importlib.util.module_from_spec(spec);spec.loader.exec_module(ccc)

class CCCReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.app=Path(self.tmp.name)/'CCC app.app';(self.app/'Contents/MacOS').mkdir(parents=True)
        (self.app/'Contents/MacOS/ccc').write_text('not executed')
        with (self.app/'Contents/Info.plist').open('wb') as f:plistlib.dump({'CFBundleIdentifier':'com.bombich.ccc','CFBundleShortVersionString':'7.2.2'},f)
    def test_exact_read_only_command_allowlist_and_quoted_paths(self):
        calls=[]
        def runner(command,**kwargs):
            calls.append(command);return subprocess.CompletedProcess(command,0,'task name | with symbols','')
        result=ccc.inspect(self.app,runner)
        self.assertEqual([x[1:] for x in calls],[['--version'],['--uuids'],['--status'],['--no-running-tasks']])
        self.assertTrue(all(x[0]==str(self.app/'Contents/MacOS/ccc') for x in calls))
        self.assertTrue(result['idle_confirmed']);self.assertFalse(result['changes_made'])
    def test_timeout_is_unknown_not_idle(self):
        def runner(command,**kwargs):raise subprocess.TimeoutExpired(command,15)
        result=ccc.inspect(self.app,runner)
        self.assertFalse(result['idle_confirmed']);self.assertFalse(result['inventory_complete'])
    def test_nonzero_idle_is_not_success(self):
        def runner(command,**kwargs):return subprocess.CompletedProcess(command,1 if '--no-running-tasks' in command else 0,'','error or running')
        self.assertFalse(ccc.inspect(self.app,runner)['idle_confirmed'])
    def test_wrong_bundle_rejected_before_invocation(self):
        with (self.app/'Contents/Info.plist').open('wb') as f:plistlib.dump({'CFBundleIdentifier':'something.else'},f)
        def runner(*args,**kwargs):self.fail('Unexpected CLI invocation')
        with self.assertRaisesRegex(ValueError,'identifier'):ccc.inspect(self.app,runner)

if __name__=='__main__':unittest.main()
