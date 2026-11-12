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


def offshoot_session():
    """Forget previous selections when OffShoot itself restarts."""
    pids = subprocess.run(['/usr/bin/pgrep', '-x', 'OffShoot'],
                          capture_output=True, text=True, timeout=3).stdout.split()
    if len(pids) != 1:
        return None
    started = subprocess.run(['/bin/ps', '-p', pids[0], '-o', 'lstart='],
                             capture_output=True, text=True, timeout=3).stdout.strip()
    return f'{pids[0]} {started}' if started else None


def remembered_sources(path, session, mounted):
    try:
        data = json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return set()
    if not session or not isinstance(data, dict) or data.get('session') != session:
        return set()
    records = data.get('records')
    if not isinstance(records, list):
        return set()
    return {record for record in records
            if isinstance(record, str) and record.split('\t', 1)[0] in mounted}


def add_sources(records, config, api, inspect_candidate=candidate, remembered=None):
    if remembered is None:
        remembered = set()
    available = []
    accepted = set()
    removed = []
    for record in dict.fromkeys(records):
        if record in remembered:
            continue
        path = Path(record.split('\t', 1)[0])
        if inspect_candidate(path, config) == record:
            available.append(str(path))
            accepted.add(record)
        else:
            removed.append(str(path))
    if available:
        api('setSource', paths=available)
        remembered.update(accepted)
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
        root = (home / 'current').resolve(strict=True)
        if root.parent != home / 'releases':
            raise ValueError('Invalid managed release')
        sys.path.insert(0, str(root))
        from ditnotes.atomic import atomic_json

        runtime = home / 'shared/runtime'
        state = runtime / 'ingest-card-sources.json'
        with (runtime / 'ingest-card-sources.lock').open('a+') as state_lock:
            fcntl.flock(state_lock, fcntl.LOCK_EX)
            paths = sorted(VOLUMES.iterdir())
            session = offshoot_session()
            remembered = remembered_sources(state, session, {str(path) for path in paths})
            previous = set(remembered)
            if args.action == 'list':
                for path in paths:
                    if (record := candidate(path, config)) and record not in remembered:
                        print(record)
            else:
                if not session:
                    raise RuntimeError('Open OffShoot before setting sources.')
                from setup_workflow import api
                unavailable = add_sources(args.paths, config, api, remembered=remembered)
                if remembered != previous and offshoot_session() != session:
                    raise RuntimeError('OffShoot restarted while setting sources. Review its Sources before trying again.')
                for path in unavailable:
                    print(path)
            # Forget observed unmounts, and write new selections only after acknowledgment.
            if session and (remembered != previous or state.exists()):
                payload = {'session': session, 'records': sorted(remembered)}
                try:
                    unchanged = json.loads(state.read_text()) == payload
                except (FileNotFoundError, ValueError):
                    unchanged = False
                if not unchanged:
                    atomic_json(state, payload)



if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
