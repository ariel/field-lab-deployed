"""Reject SQLite builds affected by the upstream WAL-reset corruption bug.

Official fix: https://www.sqlite.org/wal.html#walreset
Uses the same stdlib sqlite3 engine for metadata, queues and derived caches.
"""
import sqlite3

def version_supported(version):
    try:
        parts=tuple(int(x) for x in str(version).split('.'))
    except (ValueError,TypeError):return False
    if len(parts)!=3 or any(x<0 for x in parts):return False
    return parts>=(3,51,3) or (parts[:2]==(3,50) and parts[2]>=7) or (parts[:2]==(3,44) and parts[2]>=6)

def readiness():
    version=sqlite3.sqlite_version
    return {'ready':version_supported(version),'version':version,'required':'3.51.3+ or verified 3.50.7+/3.44.6+ backport','source':'https://www.sqlite.org/wal.html#walreset'}

def require_safe_sqlite():
    status=readiness()
    if not status['ready']:
        # RuntimeError intentionally avoids queue DatabaseError/corruption recovery:
        # an old interpreter must never cause a healthy queue to be quarantined.
        raise RuntimeError('SQLite '+status['version']+' lacks the upstream WAL-reset fix; use the bundled patched Python runtime')
    return status
