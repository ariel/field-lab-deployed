import hashlib,json,tempfile,unittest
from pathlib import Path
from ditnotes.library import _seal,_valid_object

class FinderCache(unittest.TestCase):
 def test_finder_cache_is_not_sealed_but_ai_outputs_are(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'result.json').write_text(json.dumps({'status':'complete'}));(p/'.DS_Store').write_bytes(b'finder')
   _seal(p,'content','profile','clip.mp4',{})
   self.assertNotIn('.DS_Store',json.loads((p/'complete.json').read_text())['files'])
   (p/'.DS_Store').write_bytes(b'changed');self.assertTrue(_valid_object(p,'content','profile'))
   (p/'result.json').write_text('{}');self.assertFalse(_valid_object(p,'content','profile'))
 def test_legacy_seal_remains_valid_after_finder_changes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'result.json').write_text(json.dumps({'status':'complete'}));_seal(p,'content','profile','clip.mp4',{})
   c=json.loads((p/'complete.json').read_text());c['files']['.DS_Store']={'size':3,'sha256':hashlib.sha256(b'old').hexdigest()};(p/'complete.json').write_text(json.dumps(c))
   (p/'.DS_Store').write_bytes(b'new');self.assertTrue(_valid_object(p,'content','profile'))

if __name__=='__main__':unittest.main()
