#!/usr/bin/env python3
"""Prepare one isolated release. No host services, app settings or media are touched."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, tarfile, tempfile, urllib.request, uuid
from pathlib import Path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative(root, name):
    name = Path(name)
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('Unsafe relative path: ' + str(name))
    result = Path(root) / name
    if not result.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Path escapes root: ' + str(name))
    return result


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x') as stream:
            json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


def valid(path, spec):
    return Path(path).is_file() and ('bytes' not in spec or Path(path).stat().st_size == spec['bytes']) and sha(path) == spec['sha256']


def fetch(spec, cache, offline=False):
    """Content-addressed downloads publish only after full SHA256 validation."""
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    target = cache / spec['sha256']
    if valid(target, spec): return target
    # shell bootstrap has the same Python archive with an extension.
    shell_archive = cache / (spec['sha256'] + '.tar.gz')
    if valid(shell_archive, spec): return shell_archive
    if offline: raise RuntimeError('Offline asset missing or damaged: ' + spec['url'])
    if not spec['url'].startswith('https://'): raise ValueError('Downloads require HTTPS')
    temp = cache / (spec['sha256'] + '.' + uuid.uuid4().hex + '.part')
    try:
        with urllib.request.urlopen(spec['url'], timeout=90) as source, temp.open('xb') as dest:
            shutil.copyfileobj(source, dest, 1024 * 1024); dest.flush(); os.fsync(dest.fileno())
        if not valid(temp, spec): raise RuntimeError('Downloaded checksum mismatch: ' + spec['url'])
        os.replace(temp, target)
        return target
    finally: temp.unlink(missing_ok=True)


def extract(archive, destination):
    """Reject traversal, device files and escaping links before extracting anything."""
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        for item in tar.getmembers():
            path = relative(destination, item.name)
            if item.isdev() or item.isfifo(): raise ValueError('Unsafe special archive member')
            if item.issym():
                target = Path(item.linkname)
                if target.is_absolute() or not (path.parent / target).resolve().is_relative_to(destination.resolve()):
                    raise ValueError('Archive symlink escapes destination')
            if item.islnk(): relative(destination, item.linkname)
        tar.extractall(destination, filter='data')


def run(args, root, env):
    print('+ ' + ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=root, env=env, check=True)


def tool(spec, name, root, cache, offline):
    target = relative(root, 'tools/' + name)
    if target.is_symlink(): raise ValueError("Tool directory is a symlink")
    archive = fetch(spec, cache, offline)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=name + '-', dir=target.parent) as directory:
        staging = Path(directory); extract(archive, staging)
        source = relative(staging, spec['folder'])
        if not source.is_dir(): raise RuntimeError('Unexpected archive layout: ' + name)
        if target.exists(): shutil.rmtree(target)
        os.rename(source, target)
    return target


def build_ffmpeg(root, lock, cache, offline, env):
    """Build in an explicit space-free temporary path; publish only static tools.

    FFmpeg's generated config.sh does not quote prefixes containing spaces.
    Its build prefix is disposable and never the operator's application path.
    """
    root = Path(root).resolve(); target = relative(root, 'tools/ffmpeg')
    if target.is_symlink(): raise ValueError('FFmpeg directory may not be a symlink')
    if all((target / 'bin' / name).is_file() for name in ('ffmpeg', 'ffprobe')): return target
    archive = fetch(lock['ffmpeg'], cache, offline)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Explicit dir ignores an operator TMPDIR with spaces or shell metacharacters.
    with tempfile.TemporaryDirectory(prefix='field-lab-ffmpeg-', dir='/private/tmp') as directory:
        work = Path(directory); extract(archive, work)
        source = relative(work, lock['ffmpeg']['folder']); prefix = work / 'install'
        (work / 'tmp').mkdir(); build_env = dict(env, TMPDIR=str(work / 'tmp'))
        run([source / 'configure', '--prefix=' + str(prefix), '--disable-autodetect', '--disable-doc', '--disable-ffplay', '--disable-debug', '--disable-x86asm', '--enable-small', '--enable-videotoolbox', '--enable-audiotoolbox'], source, build_env)
        run(['/usr/bin/make', '-j2'], source, build_env)
        run(['/usr/bin/make', 'install'], source, build_env)
        binaries = [prefix / 'bin' / name for name in ('ffmpeg', 'ffprobe')]
        if any(not path.is_file() or path.is_symlink() for path in binaries):
            raise RuntimeError('FFmpeg source build did not produce both standalone binaries')
        staging = target.parent / ('.ffmpeg-stage-' + uuid.uuid4().hex)
        try:
            (staging / 'bin').mkdir(parents=True)
            for source_bin in binaries:
                dest = staging / 'bin' / source_bin.name; shutil.copy2(source_bin, dest)
                with dest.open('rb') as stream: os.fsync(stream.fileno())
            # Preserve an interrupted candidate's diagnostic artifacts; no active
            # release can reach this function because prepare rejects it first.
            if target.exists(): target.rename(target.with_name('ffmpeg-incomplete-' + uuid.uuid4().hex))
            os.replace(staging, target)
            fd = os.open(target.parent, os.O_RDONLY)
            try: os.fsync(fd)
            finally: os.close(fd)
        finally:
            if staging.exists(): shutil.rmtree(staging)
    return target

def verify_models(root, lock):
    return [row['path'] for row in lock['model_files'] if not valid(relative(root / 'models', row['path']), row)]


def install_models(root, lock, cache, offline):
    missing = verify_models(root, lock)
    # Never repair a generation being used by current. Preparation of another generation is isolated.
    manifest = json.loads((root / '.field-lab-release.json').read_text())
    home = Path(manifest.get('home', root.parent.parent))
    current = home / 'current'
    if missing and current.exists() and (current / 'models').resolve() == (root / 'models').resolve():
        raise RuntimeError('Active model generation is incomplete. Stop processing and use a new release/model generation; it will not be repaired in place.')
    for row in lock['model_files']:
        path = relative(root / 'models', row['path'])
        if valid(path, row) or row.get('generated'): continue
        downloaded = fetch(row, cache, offline); path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_name(path.name + '.' + uuid.uuid4().hex + '.part')
        try:
            shutil.copyfile(downloaded, part)
            with part.open('rb') as stream: os.fsync(stream.fileno())
            os.replace(part, path)
        finally: part.unlink(missing_ok=True)
    for name, value in lock['model_json'].items():
        path = relative(root / 'models', name)
        if not path.exists(): save(path, value)
        elif json.loads(path.read_text()) != value:
            raise RuntimeError('Prepared model manifest differs from release lock: ' + name)


def prepare(root, cache, offline=False):
    root = Path(root).resolve(); lock = json.loads((root / 'deploy/assets.lock.json').read_text())
    manifest = json.loads((root / '.field-lab-release.json').read_text()) if (root / '.field-lab-release.json').exists() else {}
    home = Path(manifest.get('home', root.parent.parent))
    if (home / 'current').exists() and (home / 'current').resolve() == root:
        raise RuntimeError('Cannot prepare the active release; stage a new release or use --check.')
    for name in ['tools', 'bin', '.venv', '.conversion-venv', 'viewer/dist', 'viewer/node_modules', 'search/node_modules', 'native-progress/dist']:
        path = relative(root, name)
        if path.is_symlink(): raise ValueError('Generated directory may not be a symlink: ' + name)
    receipt = root / 'deploy-ready.json'; receipt.unlink(missing_ok=True)
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('This release requires an Apple Silicon Mac')
    if int(platform.mac_ver()[0].split('.')[0]) < lock['platform']['minimum_macos']:
        raise RuntimeError('This release requires macOS ' + str(lock['platform']['minimum_macos']) + '+')
    if subprocess.run(['/usr/bin/xcrun', '--find', 'swiftc'], capture_output=True).returncode:
        raise RuntimeError('Apple Command Line Tools are required; run xcode-select --install, complete installation, then retry.')
    # A failed/interrupted candidate can be retried. It has never been activated.
    python = tool(lock['python'], 'python', root, cache, offline) / 'bin/python3'
    node = tool(lock['node'], 'node', root, cache, offline)
    uv = tool(lock['uv'], 'uv', root, cache, offline) / 'uv'
    env = dict(os.environ, PATH=str(root / 'bin') + ':' + str(node / 'bin') + ':' + str(uv.parent) + ':' + os.environ.get('PATH', '/usr/bin:/bin'))
    if offline: env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', UV_OFFLINE='1')
    (root / 'bin').mkdir(exist_ok=True)
    for name in ['node', 'npm', 'npx']:
        target = root / 'bin' / name
        if not target.exists(): target.symlink_to(os.path.relpath(node / 'bin' / name, target.parent))
    run([python, '-c', 'import sqlite3; assert sqlite3.sqlite_version_info >= (3,53,1), sqlite3.sqlite_version'], root, env)
    if not (root / '.venv/bin/python').exists(): run([uv, 'venv', root / '.venv', '--python', python], root, env)
    run([uv, 'pip', 'sync', '--python', root / '.venv/bin/python', root / 'requirements.lock.txt'], root, env)
    for part in ['search', 'viewer']:
        args = [node / 'bin/npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund']
        if offline: args.append('--offline')
        run(args, root / part, env)
    run([node / 'bin/npm', 'run', 'build'], root / 'viewer', env)
    # Build LGPL FFmpeg with a disposable prefix, then relocate static binaries.
    ffmpeg = build_ffmpeg(root, lock, cache, offline, env)
    for name in ['ffmpeg', 'ffprobe']:
        target = root / 'bin' / name
        if not target.exists(): target.symlink_to(os.path.relpath(ffmpeg / 'bin' / name, target.parent))
        run([target, '-version'], root, env)
    run(['/usr/bin/xcrun', 'swiftc', '-O', root / 'ditnotes/native/feature_select.swift', '-o', root / 'ditnotes/native/feature_select'], root, env)
    run(['/usr/bin/swift', 'build', '--jobs', '2'], root / 'native-progress', env)
    binary_path = subprocess.check_output(['/usr/bin/swift', 'build', '--show-bin-path'], cwd=root / 'native-progress', env=env, text=True).strip()
    app = root / 'native-progress/dist/IndexerProgress.app/Contents'
    (app / 'MacOS').mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(binary_path) / 'IndexerProgress', app / 'MacOS/IndexerProgress')
    import plistlib
    with (app / 'Info.plist').open('wb') as stream:
        plistlib.dump({'CFBundleExecutable':'IndexerProgress','CFBundleIdentifier':'local.fieldlab.IndexerProgress','CFBundleName':'AI Indexer','CFBundlePackageType':'APPL','LSMinimumSystemVersion':'14.0','NSPrincipalClass':'NSApplication','NSAppTransportSecurity':{'NSAllowsLocalNetworking':True}}, stream)
    install_models(root, lock, cache, offline)
    if offline and verify_models(root, lock):
        raise RuntimeError('Offline model generation is incomplete; run preparation while connected first.')
    if not offline and not valid(root / 'models/mlx-search/clip/model.safetensors', next(x for x in lock['model_files'] if x['path'] == 'mlx-search/clip/model.safetensors')):
        spec = lock['clip_source']; downloaded = fetch(spec, cache)
        target = root / 'models/mlx-search/clip/.source/pytorch_model.bin'; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(downloaded, target)
    # Existing converter is pinned, isolated and reused; all configs are already verified above.
    if not offline:
        run([root / '.venv/bin/python', root / 'prepare_mlx_clip.py'], root, env)
        run([root / '.venv/bin/python', root / 'prepare_search.py'], root, env)
    for script, marker in [('prepare_mlx_text.py', 'mlx-text-readiness.json'), ('prepare_mlx_clip.py', 'mlx-clip-readiness.json'), ('prepare_search.py', 'search-readiness.json')]:
        if not (root / 'models/.runtime' / marker).is_file():
            run([root / '.venv/bin/python', root / script, '--check'], root, env)
    missing = verify_models(root, lock)
    if missing: raise RuntimeError('Model integrity verification failed: ' + ', '.join(missing))
    status = check(root)
    if not status['ready']: raise RuntimeError('Offline readiness failed')
    release_id = json.loads((root / '.field-lab-release.json').read_text())['release_id']
    generated = {}
    for name in ['.venv/pyvenv.cfg','tools/python/bin/python3.12','tools/node/bin/node','tools/uv/uv','tools/ffmpeg/bin/ffmpeg','tools/ffmpeg/bin/ffprobe','ditnotes/native/feature_select','native-progress/dist/IndexerProgress.app/Contents/MacOS/IndexerProgress','native-progress/dist/IndexerProgress.app/Contents/Info.plist']:
        generated[name] = sha(root / name)
    for directory in ['viewer/dist', '.venv', 'tools/python', 'tools/node', 'tools/uv', 'search/node_modules', 'viewer/node_modules']:
        for path in (root / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc': generated[str(path.relative_to(root))] = sha(path)
    save(receipt, {'release_id':release_id, 'ready':True, 'generated_files':generated, 'model_lock_sha256':sha(root / 'deploy/assets.lock.json'), 'model_files_verified':len(lock['model_files']), 'offline_readiness':status})
    return {'ready':True, 'release':str(root), 'model_files_verified':len(lock['model_files'])}


def check(root):
    root = Path(root).resolve(); lock = json.loads((root / 'deploy/assets.lock.json').read_text())
    missing = verify_models(root, lock)
    if missing: return {'ready':False, 'missing_or_damaged_models':missing}
    result = subprocess.run([root / '.venv/bin/python', root / 'dit_notes.py', 'prepare-offline', '--check'], cwd=root, capture_output=True, text=True, env=dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1'))
    try: status = json.loads(result.stdout)
    except ValueError: return {'ready':False, 'error':result.stderr or result.stdout}
    status['ready'] = bool(status.get('ready')) and result.returncode == 0
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--cache', type=Path, default=Path.home() / 'Library/Caches/Field Lab')
    parser.add_argument('--offline', action='store_true'); parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        if args.check:
            result = check(args.release)
        else:
            import fcntl
            lock_path = args.release.parent / '.bootstrap.lock'
            with lock_path.open('a+') as lock_file:
                try: fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: raise RuntimeError('Another bootstrap is running; retry after it completes.')
                result = prepare(args.release, args.cache, args.offline)
        print(json.dumps(result, indent=2)); return 0 if result['ready'] else 1
    except Exception as exc:
        print(str(exc), file=sys.stderr); return 1
if __name__ == '__main__': raise SystemExit(main())
