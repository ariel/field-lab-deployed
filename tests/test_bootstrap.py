"""Isolated disaster cases; no host app, production service or media mutations."""
import hashlib, importlib.util, io, json, tarfile, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('bootstrap',Path(__file__).resolve().parents[1]/'deploy/bootstrap.py')
b=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(b)

class BootstrapTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def archive(self,name,kind=None,link=None):
  output=self.root/'asset.tar'
  with tarfile.open(output,'w') as tar:
   item=tarfile.TarInfo(name)
   if kind:item.type=kind;item.linkname=link or ''
   else:item.size=1
   tar.addfile(item,None if kind else io.BytesIO(b'x'))
  return output
 def test_reject_traversal(self):
  for name in ['../escape','/absolute']:
   with self.assertRaises(ValueError):b.extract(self.archive(name),self.root/'dest')
  self.assertFalse((self.root/'escape').exists())
 def test_reject_escaping_symlink(self):
  with self.assertRaises(ValueError):b.extract(self.archive('link',tarfile.SYMTYPE,'../../escape'),self.root/'dest')
 def test_reject_device(self):
  with self.assertRaises(ValueError):b.extract(self.archive('device',tarfile.CHRTYPE),self.root/'dest')
 def test_valid_internal_symlink(self):
  b.extract(self.archive('folder/link',tarfile.SYMTYPE,'../target'),self.root/'dest')
  self.assertTrue((self.root/'dest/folder/link').is_symlink())
 def test_preexisting_symlink_escape(self):
  dest=self.root/'dest';dest.mkdir();(dest/'evil').symlink_to(self.root)
  with self.assertRaises(ValueError):b.extract(self.archive('evil/escape'),dest)
 def test_cache_tamper_fails_closed_offline(self):
  digest=hashlib.sha256(b'ok').hexdigest();(self.root/digest).write_bytes(b'no')
  with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
   with self.assertRaisesRegex(RuntimeError,'Offline asset'):b.fetch({'url':'https://example.test/file','sha256':digest},self.root,True)
 def test_cached_asset_no_network(self):
  digest=hashlib.sha256(b'ok').hexdigest();(self.root/digest).write_bytes(b'ok')
  with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
   self.assertEqual(b.fetch({'url':'https://example.test/file','sha256':digest},self.root,True),self.root/digest)
 def test_download_mismatch_not_published(self):
  spec={'url':'https://example.test/file','sha256':'0'*64}
  with patch('urllib.request.urlopen',return_value=io.BytesIO(b'bad')):
   with self.assertRaisesRegex(RuntimeError,'checksum'):b.fetch(spec,self.root)
  self.assertEqual(list(self.root.iterdir()),[])
 def test_model_tamper_detected_and_escape_rejected(self):
  path=self.root/'models/m';path.parent.mkdir();path.write_text('bad')
  lock={'model_files':[{'path':'m','sha256':hashlib.sha256(b'good').hexdigest()}]}
  self.assertEqual(b.verify_models(self.root,lock),['m'])
  lock['model_files'][0]['path']='../outside'
  with self.assertRaises(ValueError):b.verify_models(self.root,lock)
 def test_active_generation_not_repaired(self):
  home=self.root/'home';release=home/'releases/r1';release.mkdir(parents=True);models=home/'shared/models';models.mkdir(parents=True)
  (release/'models').symlink_to(models);(home/'current').symlink_to(release)
  (release/'.field-lab-release.json').write_text(json.dumps({'home':str(home)}))
  lock={'model_files':[{'path':'missing','sha256':'0'*64,'url':'https://example.test/file'}]}
  with self.assertRaisesRegex(RuntimeError,'Active model'):b.install_models(release,lock,self.root/'cache',True)
 def test_failed_prepare_removes_ready_receipt(self):
  (self.root/'deploy').mkdir();(self.root/'deploy/assets.lock.json').write_text('{}');(self.root/'deploy-ready.json').write_text('{}')
  with patch('platform.system',return_value='Linux'):
   with self.assertRaises(RuntimeError):b.prepare(self.root,self.root/'cache')
  self.assertFalse((self.root/'deploy-ready.json').exists())
 def test_active_release_receipt_preserved(self):
  home=self.root/'home';release=home/'releases/r1';release.mkdir(parents=True)
  (home/'current').symlink_to(release);(release/'deploy').mkdir()
  (release/'deploy/assets.lock.json').write_text('{}');(release/'.field-lab-release.json').write_text(json.dumps({'home':str(home)}))
  receipt=release/'deploy-ready.json';receipt.write_text('original')
  with self.assertRaisesRegex(RuntimeError,'active release'):b.prepare(release,self.root/'cache')
  self.assertEqual(receipt.read_text(),'original')
 def test_tool_reextracts_cached_tree(self):
  archive=self.archive('python/exec');digest=b.sha(archive);cache=self.root/'cache';cache.mkdir();archive.rename(cache/digest)
  target=self.root/'release/tools/python';target.mkdir(parents=True);(target/'exec').write_text('corrupt')
  result=b.tool({'url':'https://example.test/archive','sha256':digest,'folder':'python'},'python',self.root/'release',cache,True)
  self.assertEqual((result/'exec').read_text(),'x')
 def test_tools_symlink_cannot_escape(self):
  release=self.root/'release';release.mkdir();outside=self.root/'outside';outside.mkdir();(release/'tools').symlink_to(outside)
  with self.assertRaises(ValueError):b.tool({},'python',release,self.root/'cache',True)
 def test_lock_all_downloads_exact(self):
  lock=json.loads((Path(__file__).resolve().parents[1]/'deploy/assets.lock.json').read_text())
  for row in lock['model_files']:
   self.assertEqual(len(row['sha256']),64);self.assertGreater(row['bytes'],0)
   self.assertTrue(row.get('generated') or ('/resolve/' in row['url'] or '/opencv_zoo/' in row['url'] or '/mlx-examples/' in row['url']))

if __name__=='__main__':unittest.main()
