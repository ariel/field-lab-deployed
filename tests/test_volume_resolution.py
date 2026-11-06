"""Read-only diskutil resolver contracts, including APFS Data mount behavior."""
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from ditnotes.ingest_events import mac_volume_info

class VolumeResolution(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.mount=Path(self.temp.name).resolve();self.nested=self.mount/'Ingests/day/card';self.nested.mkdir(parents=True)
        self.info={'VolumeUUID':'DATA-UUID','MountPoint':str(self.mount)}
    def result(self,info,code=0):return subprocess.CompletedProcess([],code,stdout=plistlib.dumps(info),stderr=b'')
    def test_explicit_data_mount_queried_even_when_ismount_false(self):
        with patch('ditnotes.ingest_events.os.path.ismount',return_value=False) as heuristic,patch('ditnotes.ingest_events.subprocess.run',return_value=self.result(self.info)) as run:
            self.assertEqual(mac_volume_info(self.mount),self.info)
            self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[0][-1],str(self.mount));heuristic.assert_not_called()
    def test_nested_directory_errors_fall_back_to_actual_mount(self):
        queried=[]
        def command(args,**kwargs):
            queried.append(args[-1]);return self.result(self.info if args[-1]==str(self.mount) else {'Error':-1,'ErrorMessage':'Not a mount'})
        with patch('ditnotes.ingest_events.subprocess.run',side_effect=command):self.assertEqual(mac_volume_info(self.nested),self.info)
        self.assertEqual(queried,[str(self.nested),str(self.nested.parent),str(self.nested.parent.parent),str(self.mount)])
        self.assertNotIn('/',queried)
    def test_external_volume_positive_path_unchanged(self):
        external={'VolumeUUID':'EXTERNAL-UUID','MountPoint':str(self.mount),'Writable':True}
        with patch('ditnotes.ingest_events.subprocess.run',return_value=self.result(external)):
            self.assertEqual(mac_volume_info(self.nested),external)
    def test_file_path_starts_at_parent(self):
        media=self.nested/'clip.mp4';media.write_bytes(b'fixture')
        with patch('ditnotes.ingest_events.subprocess.run',return_value=self.result(self.info)) as run:
            self.assertEqual(mac_volume_info(media),self.info);self.assertEqual(run.call_args.args[0][-1],str(self.nested))
    def test_bad_returncode_and_malformed_or_incomplete_plists_are_ignored(self):
        values=[self.result(self.info,1),subprocess.CompletedProcess([],0,stdout=b'not a plist'),self.result({'VolumeUUID':'UUID-WITHOUT-MOUNT'}),self.result(self.info)]
        with patch('ditnotes.ingest_events.subprocess.run',side_effect=values) as run:
            self.assertEqual(mac_volume_info(self.nested),self.info);self.assertEqual(run.call_count,4)
    def test_unknown_queries_reach_root_and_raise_without_identity(self):
        queried=[]
        def command(args,**kwargs):queried.append(args[-1]);return self.result({'Error':-1})
        with patch('ditnotes.ingest_events.subprocess.run',side_effect=command):
            with self.assertRaisesRegex(RuntimeError,'Cannot determine'):mac_volume_info(self.nested)
        self.assertEqual(queried[-1],'/');self.assertEqual(len(queried),len(self.nested.parents)+1)
    def test_timeout_budget_bounded_to_twelve_seconds_and_five_per_query(self):
        now=[0];timeouts=[]
        def command(args,**kwargs):
            timeout=kwargs['timeout'];timeouts.append(timeout);now[0]+=timeout
            raise subprocess.TimeoutExpired(args,timeout)
        with patch('ditnotes.ingest_events.time.monotonic',side_effect=lambda:now[0]),patch('ditnotes.ingest_events.subprocess.run',side_effect=command):
            with self.assertRaises(RuntimeError):mac_volume_info(self.nested)
        self.assertEqual(timeouts,[5,5,2]);self.assertEqual(now[0],12)
    def test_wrong_device_identity_rejected_instead_of_root_substitution(self):
        root_info={'VolumeUUID':'SEALED-ROOT-UUID','MountPoint':'/'}
        original=Path.stat
        def stat(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path==Path('/'):
                values=list(value);values[2]=self.mount.stat().st_dev+1;return os.stat_result(values)
            return value
        with patch.object(Path,'stat',new=stat),patch('ditnotes.ingest_events.subprocess.run',return_value=self.result(root_info)):
            with self.assertRaises(RuntimeError):mac_volume_info(self.nested)

if __name__=='__main__':unittest.main()
