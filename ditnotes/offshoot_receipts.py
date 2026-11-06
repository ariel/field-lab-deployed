"""Strict adapter for observed OffShoot26.3 transfer-log schema1.1."""
from datetime import datetime
import hashlib,json,sqlite3
from pathlib import Path
from .atomic import atomic_json
from .ingest_events import enqueue,RejectedEvent

def receipt_event(data):
    if data.get('version')!='1.1' or not str(data.get('systemInfo','')).startswith('OffShoot '):raise ValueError('Unknown receipt schema')
    if data.get('status')!='success' or data.get('reason') is not None or data.get('verificationMode')!='source_destination':raise ValueError('Receipt does not establish successful full verification')
    assets=list(data.get('files',[]))
    for clip in data.get('clips',[]):assets.extend(clip.get('assets',[]))
    if not assets or any(a.get('status')!='verified' or a.get('reason') is not None for a in assets):raise ValueError('Receipt has unverified files')
    dest=Path(data['destination']['path'])
    for a in assets:
        path=Path(a['destination']['path'])
        if not path.is_relative_to(dest):raise ValueError('Receipt asset escapes destination')
    started=datetime.fromisoformat(data['started']).strftime('%Y%m%d%H%M%S')
    return {'FileCopyCompleted_state':'Success','FileCopyCompleted_verification_mode':'Source & Destination','FileCopyCompleted_startedAt':started,'FileCopyCompleted_sourcePaths':data['source']['paths'],'FileCopyCompleted_destinationPath':str(dest),'FileCopyCompleted_id':data['transferGroupId'],'FileCopyCompleted_presetName':data.get('preset',{}).get('name','')}

def recover(config,root):
    """Copy verified proof to drive before queue commit; rejected logs never authorize AI."""
    root=Path(root);portable=root/'runtime/receipts';portable.mkdir(parents=True,exist_ok=True)
    origins=[portable,Path.home()/'Library/Application Support/OffShoot/Transfer Logs',Path.home()/'Library/Application Support/Hedge/Transfer Logs']
    queued=0;examined=0
    with sqlite3.connect(config['queue_db'],timeout=15) as db:
        db.execute('CREATE TABLE IF NOT EXISTS receipts_seen(path TEXT PRIMARY KEY,size INTEGER,mtime INTEGER)')
        known={r[0]:(r[1],r[2]) for r in db.execute('SELECT path,size,mtime FROM receipts_seen')}
    for directory in origins:
        if not directory.is_dir() or directory.is_symlink():continue
        for path in directory.rglob('*.json'):
            if path.is_symlink():continue
            st=path.stat()
            if st.st_size>64*1024*1024 or known.get(str(path))==(st.st_size,st.st_mtime_ns):continue
            examined+=1
            try:
                data=json.loads(path.read_text());event=receipt_event(data)
                destination=Path(event['FileCopyCompleted_destinationPath'])
                if not destination.is_relative_to(Path(config['ingest_root'])):continue
                encoded=json.dumps(data,sort_keys=True).encode();digest=hashlib.sha256(encoded).hexdigest()
                if path.parent!=portable:atomic_json(portable/(digest+'.json'),data)
                _,inserted=enqueue(event,config);queued+=int(inserted)
                with sqlite3.connect(config['queue_db'],timeout=15) as db:db.execute('INSERT OR REPLACE INTO receipts_seen VALUES(?,?,?)',(str(path),st.st_size,st.st_mtime_ns))
            except (ValueError,KeyError,TypeError,OSError,RejectedEvent):continue
    return {'queued':queued,'examined':examined}
