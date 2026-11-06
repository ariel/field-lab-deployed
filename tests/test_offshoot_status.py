"""Independent readback fixtures: no app launches, settings writes or real prefs."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('offshoot_status_review',Path(__file__).resolve().parents[1]/'deploy/offshoot_status.py')
status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)

class OffShootStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'release';self.user=self.base/'user'
        (self.root/'runtime').mkdir(parents=True)
        self.info=self.base/'Info.plist';self.defaults_path=self.base/'SFIDefaults.plist'
        self.info.write_bytes(plistlib.dumps({'CFBundleIdentifier':'test.vendor.offshoot'}))
        hooks=[]
        for name in ['Started.scpt','Completed.scpt']:
            p=self.root/'runtime'/name;p.write_bytes(b'fake compiled hook');hooks.append(str(p))
        self.expected={'SFIDefaultsHedgeStartedScript':hooks[0],'SFIDefaultsFileCopyCompletedScript':hooks[1],'TransfersSettingsVerifyKey':'SourceAndDestination','SFIDefaultsDestinationDirectoryFormatIncrementer':'200'}
        (self.root/'runtime/setup-receipt.json').write_text(json.dumps({'hooks':self.expected,'counter':'200'}))
        (self.root/'config.json').write_text(json.dumps({'ingest_folder':'Trip media/Offloads'}))
        self.preset=self.user/'Library/Preferences/Hedge/Presets/Verified Ingest.hedge';self.preset.parent.mkdir(parents=True)
        self.preset_value={'folderPattern':'Trip media/Offloads/{YYYY}{MM}{DD}/{Source Name}-{Counter}','counter':'200','renamePattern':'','flattenFolders':False,'ignoreEmptyFolders':False,'ignoreBundles':[''],'doNotCopyFiles':[]}
        self.save_preset()
        self.defaults={**self.expected,'SFIDefaultsCurrentOrganizePreset':'Verified Ingest'};self.saved={}

    def save_preset(self):self.preset.write_text(json.dumps([self.preset_value]))

    @contextmanager
    def mocked(self,export_error=None):
        self.defaults_path.write_bytes(plistlib.dumps(self.defaults))
        mappings={'/Applications/OffShoot.app/Contents/Info.plist':self.info,'/Applications/OffShoot.app/Contents/Resources/SFIDefaults.plist':self.defaults_path}
        def command(args,**kwargs):
            self.assertEqual(args,['/usr/bin/defaults','export','test.vendor.offshoot','-'])
            self.assertTrue(kwargs['check'])
            if export_error:raise export_error
            return subprocess.CompletedProcess(args,0,stdout=plistlib.dumps(self.saved),stderr=b'')
        with patch.object(status,'Path') as path,patch.object(status.subprocess,'run',side_effect=command):
            path.side_effect=lambda p:Path(mappings.get(str(p),p));path.home.return_value=self.user
            yield

    def test_vendor_defaults_fill_unwritten_user_preferences(self):
        with self.mocked():result=status.inspect(self.root)
        self.assertTrue(result['settings_verified']);self.assertEqual(result['mismatches'],[])
        self.assertIn('actual destination',result['destination_validation']);self.assertFalse(result['ccc_changed'])

    def test_user_setting_override_reports_mismatch(self):
        self.saved={'TransfersSettingsVerifyKey':'Transfer'}
        with self.mocked():result=status.inspect(self.root)
        self.assertFalse(result['settings_verified']);self.assertEqual(result['mismatches'][0]['key'],'TransfersSettingsVerifyKey')

    def test_counter_may_advance_but_not_regress(self):
        for value,expected in [('201',True),('199',False),('not a number',False)]:
            with self.subTest(counter=value):
                self.saved={'SFIDefaultsDestinationDirectoryFormatIncrementer':value}
                with self.mocked():result=status.inspect(self.root)
                self.assertEqual(result['settings_verified'],expected)

    def test_missing_hook_is_not_ready(self):
        Path(self.expected['SFIDefaultsFileCopyCompletedScript']).unlink()
        with self.mocked():result=status.inspect(self.root)
        self.assertFalse(result['hook_files_present']);self.assertFalse(result['settings_verified'])

    def test_wrong_active_preset_is_not_ready(self):
        self.saved={'SFIDefaultsCurrentOrganizePreset':'Different Preset'}
        with self.mocked():result=status.inspect(self.root)
        self.assertFalse(result['active_preset_matches']);self.assertFalse(result['settings_verified'])

    def test_wrong_folder_or_flattening_is_not_ready(self):
        for key,value in [('folderPattern','Elsewhere/{Counter}'),('flattenFolders',True),('renamePattern','new-{Filename}')]:
            original=self.preset_value.copy();self.preset_value[key]=value;self.save_preset()
            with self.mocked():result=status.inspect(self.root)
            self.assertFalse(result['settings_verified']);self.preset_value=original

    def test_selective_copy_or_preset_counter_regression_is_not_ready(self):
        for key,value in [('copyOnlyFiles',['mp4']),('doNotCopyFiles',['xml']),('ignoreEmptyFolders',True),('ignoreBundles',['AVCHD<2MB']),('counter','199')]:
            with self.subTest(key=key):
                original=self.preset_value.copy();self.preset_value[key]=value;self.save_preset()
                with self.mocked():result=status.inspect(self.root)
                self.assertFalse(result['preset_matches']);self.assertFalse(result['settings_verified'])
                self.preset_value=original

    def test_nonmapping_preferences_are_unknown_not_ready(self):
        self.saved=[]
        with self.mocked():
            with self.assertRaisesRegex(ValueError,'mapping'):status.inspect(self.root)

    def test_unavailable_pref_export_is_unknown_not_ready(self):
        error=subprocess.CalledProcessError(1,['defaults','export'])
        with self.mocked(export_error=error):
            with self.assertRaises(subprocess.CalledProcessError):status.inspect(self.root)

    def test_corrupt_receipt_is_not_success(self):
        (self.root/'runtime/setup-receipt.json').write_text('{broken')
        with self.mocked():
            with self.assertRaises(ValueError):status.inspect(self.root)

if __name__=='__main__':unittest.main()
