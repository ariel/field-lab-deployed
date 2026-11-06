"""Real configure/make/install fixture for homes, caches and TMPDIR with spaces."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bootstrap_paths_subject',ROOT/'deploy/bootstrap.py')
bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap)

CONFIGURE=r'''#!/bin/sh
set -eu
for arg do
  case "$arg" in --prefix=*) prefix=${arg#*=} ;; esac
done
mkdir -p ffbuild
# Reproduce the real FFmpeg config.sh prefix quoting limitation.
printf 'prefix=%s\n' "$prefix" > ffbuild/config.sh
printf 'prefix = %s\n' "$prefix" > Makefile
cat >> Makefile <<'MAKE'
all:
	@/bin/sh -ec '. ./ffbuild/config.sh; test -n "$$prefix"'
install: all
	@mkdir -p "$(prefix)/bin" "$(prefix)/lib/pkgconfig"
	@printf '#!/bin/sh\necho build-prefix=%s\n' "$(prefix)" > "$(prefix)/bin/ffmpeg"
	@chmod +x "$(prefix)/bin/ffmpeg"
	@if [ "$${SKIP_PROBE:-0}" != 1 ]; then cp "$(prefix)/bin/ffmpeg" "$(prefix)/bin/ffprobe"; fi
	@printf 'do not publish disposable build prefixes\n' > "$(prefix)/lib/pkgconfig/fake.pc"
MAKE
'''

@unittest.skipUnless(Path('/private/tmp').is_dir() and Path('/usr/bin/make').is_file(),'macOS build fixture')
class BootstrapPaths(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='Field Lab path fixture ');self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.root=self.base/'Ariel’s Application Support/Field Lab';self.root.mkdir(parents=True)
        self.cache=self.base/'Download Cache with spaces';self.cache.mkdir()
        source=self.base/'fixture-source';source.mkdir();(source/'configure').write_text(CONFIGURE);(source/'configure').chmod(0o755)
        archive=self.base/'fixture.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:tar.add(source,arcname='ffmpeg-fixture')
        sha=hashlib.sha256(archive.read_bytes()).hexdigest();(self.cache/sha).write_bytes(archive.read_bytes())
        self.lock={'ffmpeg':{'url':'https://example.invalid/never-download','sha256':sha,'folder':'ffmpeg-fixture'}}
        self.tmpdir=self.base/'Temporary Files with spaces';self.tmpdir.mkdir()
        self.env=dict(os.environ,TMPDIR=str(self.tmpdir))
    def test_build_and_relocated_binaries_work_in_space_home(self):
        with patch.dict(os.environ,{'TMPDIR':str(self.tmpdir)}):
            target=bootstrap.build_ffmpeg(self.root,self.lock,self.cache,True,self.env)
        self.assertEqual(target,self.root/'tools/ffmpeg')
        for name in ('ffmpeg','ffprobe'):
            output=subprocess.check_output([target/'bin'/name,'-version'],text=True).strip()
            self.assertTrue(output.startswith('build-prefix=/private/tmp/field-lab-ffmpeg-'))
            prefix=Path(output.split('=',1)[1]);self.assertNotIn(' ',str(prefix));self.assertFalse(prefix.exists())
        self.assertFalse((target/'lib').exists(),'Disposable build package metadata must not ship')
        self.assertEqual(sorted(p.name for p in target.iterdir()),['bin'])
    def test_missing_binary_does_not_publish_incomplete_tool(self):
        target=self.root/'tools/ffmpeg';target.mkdir(parents=True);(target/'diagnostic').write_text('old incomplete build')
        env=dict(self.env,SKIP_PROBE='1')
        with self.assertRaisesRegex(RuntimeError,'both standalone binaries'):
            bootstrap.build_ffmpeg(self.root,self.lock,self.cache,True,env)
        self.assertEqual((target/'diagnostic').read_text(),'old incomplete build');self.assertFalse((target/'bin').exists())
    def test_rebuild_preserves_old_diagnostics(self):
        target=self.root/'tools/ffmpeg';target.mkdir(parents=True);(target/'diagnostic').write_text('earlier failure')
        bootstrap.build_ffmpeg(self.root,self.lock,self.cache,True,self.env)
        preserved=list((self.root/'tools').glob('ffmpeg-incomplete-*'))
        self.assertEqual(len(preserved),1);self.assertEqual((preserved[0]/'diagnostic').read_text(),'earlier failure')

if __name__=='__main__':unittest.main()
