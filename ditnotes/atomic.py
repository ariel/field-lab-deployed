"""Same-filesystem durable publication primitives."""
import json
import os
from pathlib import Path
import uuid


def fsync_dir(path):
    fd=os.open(path,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    part=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with part.open('x') as handle:
            json.dump(data,handle,ensure_ascii=False,indent=2);handle.write('\n')
            handle.flush();os.fsync(handle.fileno())
        os.replace(part,path);fsync_dir(path.parent)
    finally:
        if part.exists():part.unlink()


def fsync_tree(root):
    root=Path(root)
    for path in root.rglob('*'):
        if path.is_symlink():raise ValueError('Generated output must not contain symlinks')
        if path.is_file():
            with path.open('rb') as handle:os.fsync(handle.fileno())
    for path in sorted((p for p in root.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):fsync_dir(path)
    fsync_dir(root)
