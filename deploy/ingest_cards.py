"""Discover mounted camera-card candidates and pass confirmed sources to OffShoot."""
import argparse
import fcntl
import json
from pathlib import Path
import plistlib
import subprocess
import sys

VOLUMES = Path('/Volumes')


def disk_info(path):
    result = subprocess.run(
        ['/usr/sbin/diskutil', 'info', '-plist', str(path)],
        capture_output=True, timeout=5,
    )
    return plistlib.loads(result.stdout) if result.returncode == 0 else {}


def candidate(path, config, inspect=disk_info):
    # Volume names are passed as individual lines to the applet's picker.
    if path.parent != VOLUMES or path.is_symlink() or any(c in str(path) for c in '\r\n\t'):
        return None
    if str(path) == config['volume_mount']:
        return None
    try:
        info = inspect(path)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    uuid = info.get('VolumeUUID')
    if (
        info.get('MountPoint') == str(path)
        and uuid
        and uuid.casefold() != config['volume_uuid'].casefold()
        and not info.get('OSInternalMedia')
        and info.get('BusProtocol') != 'Disk Image'
        and info.get('VirtualOrPhysical') != 'Virtual'
        and (info.get('RemovableMedia') or info.get('Removable') or (
            not info.get('Internal')
            and (path / 'DCIM').is_dir()
        ))
    ):
        return '\t'.join((str(path), uuid, info.get('DeviceIdentifier', '')))
    return None


def add_sources(records, config, api, inspect_candidate=candidate):
    available = []
    removed = []
    for record in dict.fromkeys(records):
        path = Path(record.split('\t', 1)[0])
        if inspect_candidate(path, config) == record:
            available.append(str(path))
        else:
            removed.append(str(path))
    if available:
        api('setSource', paths=available)
    return removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('home', type=Path)
    parser.add_argument('action', choices=['list', 'add'])
    parser.add_argument('paths', nargs='*')
    args = parser.parse_args()
    home = args.home.resolve()
    with (home / 'deploy.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        config = json.loads((home / 'shared/config.json').read_text())
        if args.action == 'list':
            for path in sorted(VOLUMES.iterdir()):
                if record := candidate(path, config):
                    print(record)
        else:
            root = (home / 'current').resolve(strict=True)
            if root.parent != home / 'releases':
                raise ValueError('Invalid managed release')
            sys.path.insert(0, str(root))
            from setup_workflow import api
            for path in add_sources(args.paths, config, api):
                print(path)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
