"""Short OffShoot event validation/enqueue; standard library only, no inference.

FileCopyCompleted is per transfer/destination, including failures. Official event
schema does not promise a transfer ID. Derive one from start time + source paths
when absent. Queue identity additionally includes destination and volume UUID.

Worker invariant: recheck volume UUID/path before claiming AND opening media;
traverse only job.destination, never the ingest root, and never follow symlinks.
A unique transfer destination folder is required. Do not process arbitrary old
files when multiple transfers reuse a folder. Keep completed queue rows for dedup.

Docs: https://docs.hedge.video/offshoot/features/automation/scripts/events/filecopycompleted
https://docs.hedge.video/offshoot/features/verification
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import sqlite3
import subprocess
import time

PREFIX = 'FileCopyCompleted_'
class RejectedEvent(ValueError):
    pass

def mac_volume_info(path):
    volume=Path(path).resolve(strict=True)
    if volume.is_file():volume=volume.parent
    device=volume.stat().st_dev
    deadline=time.monotonic()+12
    # APFS Data and firmlink-backed mounts are not reliably recognized by
    # os.path.ismount(). Ask diskutil about the explicit path first, then walk
    # ancestors only when it cannot identify that path. Never substitute the
    # sealed system volume for a Data-volume path merely because it is '/'.
    for candidate in (volume,*volume.parents):
        remaining=deadline-time.monotonic()
        if remaining<=0:break
        try:
            result=subprocess.run(['/usr/sbin/diskutil','info','-plist',str(candidate)],
                                  check=False,capture_output=True,timeout=min(5,remaining))
            if result.returncode:continue
            info=plistlib.loads(result.stdout)
            if not isinstance(info,dict) or any(str(k).lower().startswith('error') and v for k,v in info.items()):continue
            identity=info.get('VolumeUUID');mount=info.get('MountPoint')
            if not isinstance(identity,str) or not identity.strip() or not isinstance(mount,str) or not mount.startswith('/'):continue
            mounted=Path(mount).resolve(strict=True)
            if not mounted.is_dir() or mounted.stat().st_dev!=device:continue
            return info
        except (OSError,ValueError,TypeError,plistlib.InvalidFileException,subprocess.SubprocessError):
            continue
    raise RuntimeError('Cannot determine the mounted volume for '+str(volume)+' within the diskutil query budget')

def _required(event, key):
    value = event.get(PREFIX + key)
    if not isinstance(value, str) or not value.strip():
        raise RejectedEvent('missing_or_invalid_' + key)
    return value.strip()

def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def validate_event(event, config, volume_probe=mac_volume_info):
    if not isinstance(event, dict):
        raise RejectedEvent('event_must_be_object')
    if _required(event, 'state') != 'Success':
        raise RejectedEvent('transfer_not_successful')
    # SourceAndDestination is the documented API preference spelling; event
    # examples use Source & Destination. Transfer/Source are not equivalent.
    mode = _required(event, 'verification_mode')
    if mode not in ('Source & Destination', 'SourceAndDestination'):
        raise RejectedEvent('full_source_destination_verification_required')
    started = _required(event, 'startedAt')
    if not re.fullmatch(r'\d{14}', started):
        raise RejectedEvent('invalid_startedAt')
    sources = event.get(PREFIX+'sourcePaths')
    if isinstance(sources,list) and sources and all(isinstance(p,str) and p.startswith('/') for p in sources):
        sources=json.dumps(sorted(sources),separators=(',',':'))
    elif isinstance(sources,str) and sources.strip():
        sources=sources.strip()
    else:raise RejectedEvent('missing_or_invalid_sourcePaths')
    mount = Path(config['volume_mount']).resolve(strict=True)
    root = Path(config['ingest_root']).resolve(strict=True)
    destination = Path(_required(event, 'destinationPath'))
    if not destination.is_absolute():
        raise RejectedEvent('destination_must_be_absolute')
    destination = destination.resolve(strict=True)
    if root == mount or not root.is_relative_to(mount):
        raise RejectedEvent('ingest_root_must_be_subfolder_of_volume')
    if destination == root or not destination.is_relative_to(root):
        raise RejectedEvent('destination_must_be_dedicated_ingest_subfolder')
    expected_uuid = str(config['volume_uuid']).strip().upper()
    if not expected_uuid:
        raise RejectedEvent('volume_uuid_required')
    for path in (mount, destination):
        info = volume_probe(path)
        if str(info.get('VolumeUUID', '')).upper() != expected_uuid:
            raise RejectedEvent('volume_uuid_mismatch')
        if not info.get('MountPoint') or Path(info['MountPoint']).resolve() != mount:
            raise RejectedEvent('volume_mount_mismatch')
    if destination.stat().st_dev != mount.stat().st_dev:
        raise RejectedEvent('destination_device_mismatch')
    explicit = event.get(PREFIX + 'id') or event.get(PREFIX + 'transferId')
    transfer_id = str(explicit) if explicit else _digest({'started_at': started, 'source_paths': sources})
    identity = {'started_at': started, 'source_paths': sources, 'destination': str(destination), 'volume_uuid': expected_uuid}
    return {'schema_version': 1, 'job_id': _digest(identity), **identity, 'transfer_id':transfer_id,
            'identity_origin': 'event_transferId' if explicit else 'derived_start_and_sources',
            'ingest_root': str(root), 'volume_mount': str(mount),
            'started_at': started, 'source_paths': sources,
            'verification_mode': 'Source & Destination', 'state': 'pending',
            'event': event, 'enqueued_at': time.time()}

def enqueue(event, config, volume_probe=mac_volume_info):
    """Commit one idempotent job. Returns (job, inserted). No directory traversal.

    queue_db belongs on the Mac's local disk. SQLite locks coordinate concurrent
    hooks; FULL synchronous WAL commits persist before success is returned.
    A crash is either no committed job (retry event) or one complete job.
    """
    job = validate_event(event, config, volume_probe)
    db = Path(config['queue_db']).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(db, timeout=5) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('''CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'pending',
            payload TEXT NOT NULL, enqueued_at REAL NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
            claimed_at REAL, finished_at REAL)''')
        conn.execute('BEGIN IMMEDIATE')
        cursor = conn.execute('INSERT OR IGNORE INTO jobs(job_id,state,payload,enqueued_at) VALUES(?,?,?,?)',
                              (job['job_id'], 'pending', json.dumps(job, sort_keys=True), job['enqueued_at']))
        inserted = cursor.rowcount == 1
        conn.commit()
    return job, inserted
