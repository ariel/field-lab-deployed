"""Native Desktop launchers tested only in temporary folders, never opened."""
import importlib.util,json,os,plistlib,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock

spec=importlib.util.spec_from_file_location('desktop_install_test',Path(__file__).resolve().parents[1]/'deploy/desktop.py')
desktop=importlib.util.module_from_spec(spec);spec.loader.exec_module(desktop)

class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.home=self.base/'Ariel’s "field" lab $HOME `literal`';self.dest=self.base/'Disposable Desktop';self.dest.mkdir()
        self.release=self.home/'releases'/('a'*64);self.release.mkdir(parents=True)
        (self.home/'current').symlink_to(self.release)
        (self.home/'run').write_text('not executed')
        (self.home/'shared').mkdir();(self.home/'shared/config.json').write_text('{}')
    def fake_compile(self,source,target,title,command,icon):
        script=target/'Contents/Resources/Scripts/main.scpt';script.parent.mkdir(parents=True);script.write_text(source.read_text())
        info=target/'Contents/Info.plist';info.write_bytes(plistlib.dumps({'CFBundleName':title}))
    def install(self,**kwargs):return desktop.install(self.home,self.dest,compiler=kwargs.get('compiler',self.fake_compile))
    def test_four_shortcuts_are_stable_across_release_switch(self):
        result=self.install();self.assertFalse(result['launched']);self.assertEqual(len(result['apps']),4)
        links={p.name:os.readlink(p) for p in self.dest.iterdir()}
        second=self.home/'releases'/('b'*64);second.mkdir();(self.home/'current').unlink();(self.home/'current').symlink_to(second)
        again=self.install();self.assertEqual(result['generation'],again['generation'])
        self.assertEqual(links,{p.name:os.readlink(p) for p in self.dest.iterdir()})
        for title in desktop.APPS:
            script=(self.dest/(title+'.app')/'Contents/Resources/Scripts/main.scpt').read_text()
            self.assertNotIn('/releases/',script);self.assertNotIn('addTransfers',script)
    def test_unmanaged_file_preflight_blocks_all_installation(self):
        p=self.dest/'Field Lab Ingest.app';p.write_text('user file')
        with self.assertRaisesRegex(ValueError,'not managed'):self.install()
        self.assertEqual(p.read_text(),'user file');self.assertEqual(len(list(self.dest.iterdir())),1)
        self.assertFalse((self.home/'shared/runtime/desktop-apps/current').exists())
    def test_unowned_symlink_is_not_adopted(self):
        p=self.dest/'Field Lab Library.app';p.symlink_to(self.release)
        with self.assertRaisesRegex(ValueError,'not managed'):self.install()
        self.assertEqual(os.readlink(p),str(self.release))
    def test_compiler_failure_leaves_previous_apps_and_pointer(self):
        self.install();base=self.home/'shared/runtime/desktop-apps';before=os.readlink(base/'current')
        def failure(*args):raise RuntimeError('simulated compile failure')
        with patch.object(desktop.manager,'digest',side_effect=lambda p:'new version' if Path(p)==Path(desktop.__file__) else __import__('hashlib').sha256(Path(p).read_bytes()).hexdigest()):
            with self.assertRaisesRegex(RuntimeError,'compile failure'):self.install(compiler=failure)
        self.assertEqual(os.readlink(base/'current'),before)
        self.assertTrue(all(p.exists() for p in self.dest.iterdir()))
    def test_partial_shortcut_creation_resumes_from_durable_ownership(self):
        self.install();p=self.dest/'Field Lab Library.app';p.unlink();self.install();self.assertTrue(p.is_symlink())
    def test_missing_active_config_is_not_installed(self):
        (self.home/'shared/config.json').unlink()
        with self.assertRaisesRegex(ValueError,'configure'):self.install()
        self.assertEqual(list(self.dest.iterdir()),[])
    def test_unmanaged_item_added_after_prior_install_is_preserved(self):
        self.install();p=self.dest/'Field Lab Stop AI.app';p.unlink();p.mkdir();(p/'keep').write_text('mine')
        with self.assertRaisesRegex(ValueError,'not managed'):self.install()
        self.assertEqual((p/'keep').read_text(),'mine')
    @unittest.skipUnless(Path('/usr/bin/osacompile').exists(),'macOS AppleScript compiler required')
    def test_actual_local_app_compile_sign_and_decompile_never_launch(self):
        result=self.install(compiler=desktop.compile_app)
        for title,(command,_) in desktop.APPS.items():
            app=self.dest/(title+'.app');info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
            self.assertEqual(info['CFBundleIdentifier'],'local.fieldlab.desktop.'+command)
            source=subprocess.check_output(['/usr/bin/osadecompile',str(app/'Contents/Resources/Scripts/main.scpt')],text=True)
            self.assertIn('do shell script',source);self.assertIn('display alert "Field Lab"',source)
            self.assertIn('run',source);self.assertNotIn('Terminal',source);self.assertNotIn('addTransfers',source)
            subprocess.run(['/usr/bin/codesign','--verify','--strict',str(app)],check=True,capture_output=True)
        self.assertFalse(result['launched'])

class DesktopDispatchTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('desktop_launcher_test',Path(__file__).resolve().parents[1]/'deploy/launcher.py')
        self.launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.launcher)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'config.json').write_text(json.dumps({'port':8877}))
    def test_ingest_validates_volume_opens_offshoot_and_starts_without_copy(self):
        with patch.object(self.launcher.subprocess,'run') as run:self.launcher.dispatch(self.root,'ingest')
        calls=[call.args[0] for call in run.call_args_list]
        self.assertIn('verify_volume',calls[0][-1]);self.assertEqual(calls[1],['/usr/bin/open','-a','/Applications/OffShoot.app'])
        self.assertEqual(calls[2][-1],'start')
        joined=' '.join(str(x) for command in calls for x in command)
        for forbidden in ['addTransfers','offshoot://reset','setPreferences','ccc']:self.assertNotIn(forbidden,joined)
    def test_invalid_volume_never_opens_offshoot(self):
        error=subprocess.CalledProcessError(1,['validate volume'])
        with patch.object(self.launcher.subprocess,'run',side_effect=error) as run:
            with self.assertRaises(subprocess.CalledProcessError):self.launcher.dispatch(self.root,'ingest')
        self.assertEqual(run.call_count,1)
    def test_library_waits_for_local_status_before_opening_browser(self):
        opener=MagicMock();response=MagicMock();response.__enter__.return_value.status=200
        opener.open.side_effect=[self.launcher.urllib.error.URLError('not ready'),response]
        with patch.object(self.launcher.subprocess,'run') as run,patch.object(self.launcher.urllib.request,'build_opener',return_value=opener),patch.object(self.launcher.time,'sleep') as sleep:
            self.launcher.dispatch(self.root,'library')
        self.assertEqual(run.call_args_list[0].args[0][-1],'start')
        self.assertEqual(run.call_args_list[-1].args[0],['/usr/bin/open','http://127.0.0.1:8877/'])
        self.assertEqual(opener.open.call_count,2);sleep.assert_called_once()
        self.assertEqual(opener.open.call_args.args[0],'http://127.0.0.1:8877/api/status')
    def test_library_timeout_has_no_browser_launch(self):
        opener=MagicMock();opener.open.side_effect=self.launcher.urllib.error.URLError('unavailable')
        with patch.object(self.launcher.subprocess,'run') as run,patch.object(self.launcher.urllib.request,'build_opener',return_value=opener),patch.object(self.launcher.time,'monotonic',side_effect=[0,31]):
            with self.assertRaisesRegex(RuntimeError,'did not become available'):self.launcher.dispatch(self.root,'library')
        self.assertEqual(run.call_count,1)
    def test_stop_only_stops_ai(self):
        with patch.object(self.launcher.subprocess,'run') as run:self.launcher.dispatch(self.root,'stop')
        run.assert_called_once();self.assertEqual(run.call_args.args[0][-1],'stop')

if __name__=='__main__':unittest.main()
