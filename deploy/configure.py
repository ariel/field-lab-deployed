"""Explicit per-machine configuration; never writes to source media."""
from __future__ import annotations
import argparse,json,os,plistlib,socket,subprocess,sys,tempfile
from pathlib import Path

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
        fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def machine_config(volume,folder='Ingests',port=8766,info=None):
    volume=Path(volume).expanduser().resolve()
    if not volume.is_dir():raise ValueError('Choose an existing mounted volume')
    relative=Path(folder)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0].startswith('.'):
        raise ValueError('Ingest folder must be a non-hidden relative folder inside the volume')
    project=(volume/relative).resolve()
    if project==volume or not project.is_relative_to(volume):raise ValueError('Ingest folder escapes the volume')
    if not 1024<=int(port)<=65535:raise ValueError('Port must be between 1024 and 65535')
    if info is None:
        info=plistlib.loads(subprocess.check_output(['/usr/sbin/diskutil','info','-plist',str(volume)]))
    if Path(info.get('MountPoint','')).resolve()!=volume or not info.get('VolumeUUID'):
        raise ValueError('Path must be the actual volume mount point with a stable UUID')
    # Cards must never become the ingest destination by accident.
    if info.get('ReadOnlyVolume') or info.get('Writable') is False:raise ValueError('Destination is read-only')
    return {'schema_version':1,'volume_uuid':info['VolumeUUID'],'volume_mount':str(volume),'ingest_folder':str(relative),'ingest_root':str(project),'port':int(port),'features':{'automatic_face_grouping':True,'automatic_voice_grouping':True,'automatic_note_inheritance':True,'face_named_match_threshold':.72,'identity_match_margin':.08}}

def save_config(home,config,replace=False):
    path=Path(home).expanduser().absolute()/'shared/config.json'
    if path.is_symlink():raise ValueError('Refusing symlink config destination')
    if path.exists():
        old=json.loads(path.read_text())
        if old==config:return {'changed':False,'config':old}
        if not replace:raise ValueError('Existing configuration differs; use --replace-config only for an intentional drive migration')
        raise ValueError('Drive migration requires a separate plan preserving queued receipt paths; automatic replacement is disabled')
    atomic_json(path,config)
    return {'changed':True,'config':config}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--home',type=Path,required=True);p.add_argument('--volume',required=True);p.add_argument('--ingest-folder',default='Ingests');p.add_argument('--port',type=int,default=8766);a=p.parse_args()
    print(json.dumps(save_config(a.home,machine_config(a.volume,a.ingest_folder,a.port)),indent=2))
if __name__=='__main__':main()
