#!/usr/bin/env python3
"""Install local native Desktop applets pointing at the stable managed launcher.

Compile locally; never run the applets during installation. No Terminal windows,
OffShoot API mutations, source-card operations or CCC tasks are triggered here.
"""
from __future__ import annotations
import argparse,hashlib,json,os,plistlib,shlex,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import manager

APPS={'Field Lab Ingest':('ingest','GenericHardDiskIcon.icns'),
      'Field Lab Library':('library','MovieFolderIcon.icns'),
      'Field Lab AI Progress':('progress','Clock.icns'),
      'Field Lab Stop AI':('stop','AlertStopIcon.icns')}
INGEST_FILES = Path(__file__).resolve().parent
SYSTEM_ICONS=Path('/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources')

def script(home,command):
    if command not in {v[0] for v in APPS.values()}:raise ValueError('Unsupported Desktop action')
    shell=shlex.join([str(Path(home)/'run'),command])
    if command == 'ingest':
        properties = {
            'launcherCommand': shell,
            'pythonCommand': shlex.quote(str(Path(home)/'current/.venv/bin/python')) + ' -B',
            'applicationHome': str(home),
        }
        header = ''.join(f'property {name} : {json.dumps(value, ensure_ascii=False)}\n'
                         for name, value in properties.items())
        return header + (INGEST_FILES/'ingest_cards.applescript').read_text()
    return 'try\n    do shell script '+json.dumps(shell,ensure_ascii=False)+'\non error errorMessage number errorNumber\n    display alert "Field Lab" message errorMessage as critical buttons {"OK"} default button "OK"\nend try\n'

def compile_app(source,destination,title,command,icon,runner=subprocess.run):
    options = ['-s'] if command == 'ingest' else []
    runner(['/usr/bin/osacompile', *options, '-o', str(destination), str(source)],
           check=True, capture_output=True, text=True)
    info_path=destination/'Contents/Info.plist'
    with info_path.open('rb') as stream:info=plistlib.load(stream)
    info.update(CFBundleIdentifier='local.fieldlab.desktop.'+command,CFBundleName=title,CFBundleDisplayName=title,LSUIElement=command != 'ingest')
    if command == 'ingest':
        shutil.copyfile(INGEST_FILES/'ingest_cards.py', destination/'Contents/Resources/ingest_cards.py')
        (destination/'Contents/Resources/Scripts/main.scpt').chmod(0o444)
    local_icon=SYSTEM_ICONS/icon
    if local_icon.is_file():
        shutil.copyfile(local_icon,destination/'Contents/Resources/FieldLab.icns');info['CFBundleIconFile']='FieldLab'
    with info_path.open('wb') as stream:plistlib.dump(info,stream)
    # Applets are built on the destination Mac, not distributed pre-signed.
    runner(['/usr/bin/codesign','--force','--sign','-',str(destination)],check=True,capture_output=True,text=True)
    runner(['/usr/bin/codesign','--verify','--strict',str(destination)],check=True,capture_output=True,text=True)
    if not (destination/'Contents/Resources/Scripts/main.scpt').is_file():raise ValueError('Compiled applet lacks its main script')

def _read_manifest(path):
    if path.is_symlink():raise ValueError('Refusing symlink Desktop ownership manifest')
    if not path.exists():return {'schema':1,'desktops':{}}
    data=json.loads(path.read_text())
    if data.get('schema')!=1 or not isinstance(data.get('desktops'),dict):raise ValueError('Invalid Desktop ownership manifest')
    return data

def install(home,desktop=None,compiler=compile_app):
    home=Path(home).expanduser().absolute();desktop=Path(desktop or Path.home()/'Desktop').expanduser().absolute()
    if not desktop.is_dir():raise ValueError('Desktop destination must already exist')
    desktop=desktop.resolve()
    with manager.locked(home) as (home,releases,shared):
        active=manager.pointer(home,'current')
        if active is None or not (home/'run').is_file() or not (shared/'config.json').is_file():
            raise ValueError('Activate and configure Field Lab before installing Desktop apps')
        if desktop.is_relative_to(home):raise ValueError('Desktop shortcuts must be outside the application home')
        base=manager.real_directory(shared/'runtime/desktop-apps',create=True)
        generations=manager.real_directory(base/'generations',create=True)
        current=base/'current'
        if (current.exists() or current.is_symlink()) and not current.is_symlink():raise ValueError('Desktop app pointer is unmanaged')
        if current.is_symlink() and current.resolve().parent!=generations:raise ValueError('Desktop app pointer escapes its generations')
        manifest_path=base/'ownership.json';manifest=_read_manifest(manifest_path)
        owned=manifest['desktops'].get(str(desktop),{})
        if not isinstance(owned,dict):raise ValueError('Invalid Desktop ownership entry')
        links={str(desktop/(title+'.app')):str(current/(title+'.app')) for title in APPS}
        # Complete preflight before compiling/publishing; never replace another app/file.
        for path,target in links.items():
            p=Path(path)
            if p.exists() or p.is_symlink():
                if owned.get(path)!=target or not p.is_symlink() or os.readlink(p)!=target:
                    raise ValueError('Desktop item is not managed by Field Lab: '+path)
        inputs={title:script(home,command) for title,(command,_) in APPS.items()}
        fingerprint=hashlib.sha256(json.dumps({'scripts':inputs,'installer':manager.digest(Path(__file__)),
                                               'ingest_helper':manager.digest(INGEST_FILES/'ingest_cards.py')},sort_keys=True).encode()).hexdigest()
        generation=generations/fingerprint
        if generation.exists():
            if generation.is_symlink():raise ValueError('Desktop generation cannot be a symlink')
            expected=json.loads((generation/'manifest.json').read_text())
            if expected.get('generation')!=fingerprint or not isinstance(expected.get('files'),dict) or not expected['files']:
                raise ValueError('Invalid Desktop generation manifest')
            for relative,digest in expected['files'].items():
                p=manager.safe_relative(generation,relative)
                if not p.is_file() or manager.digest(p)!=digest:raise ValueError('Desktop generation integrity failure: '+relative)
        else:
            staging=Path(tempfile.mkdtemp(prefix='.staging-',dir=generations))
            for title,(command,icon) in APPS.items():
                source=staging/(title+'.applescript');source.write_text(inputs[title])
                compiler(source,staging/(title+'.app'),title,command,icon)
            files={str(p.relative_to(staging)):manager.digest(p) for p in staging.rglob('*') if p.is_file()}
            manager.atomic_json(staging/'manifest.json',{'schema':1,'generation':fingerprint,'files':files})
            for p in staging.rglob('*'):
                if p.is_file():
                    with p.open('rb') as stream:os.fsync(stream.fileno())
            for directory,_,_ in os.walk(staging,topdown=False):manager.sync_dir(directory)
            os.rename(staging,generation);manager.sync_dir(generations)
        manager.set_pointer(base,'current',generation)
        # Persist ownership before creating links so a crash can resume without adoption.
        manifest['desktops'][str(desktop)]=links;manifest['generation']=fingerprint
        manager.atomic_json(manifest_path,manifest)
        for path,target in links.items():
            p=Path(path)
            if p.is_symlink():
                if os.readlink(p)!=target:raise ValueError('Desktop shortcut changed during installation: '+path)
            else:p.symlink_to(target,target_is_directory=True)
        manager.sync_dir(desktop)
        return {'desktop':str(desktop),'apps':list(links),'generation':fingerprint,'application_home':str(home),'launched':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--home',type=Path,default=manager.DEFAULT_HOME);parser.add_argument('--desktop',type=Path);args=parser.parse_args()
    try:print(json.dumps(install(args.home,args.desktop),indent=2));return 0
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        print(json.dumps({'error':str(exc),'launched':False}),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
