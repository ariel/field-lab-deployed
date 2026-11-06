"""Durable, content-cached search vectors and sealed catalog/vector snapshots.

Call build on the backend's serialized MLX executor; this module creates no
inference threads. A failed build never changes the current snapshot pointer.
"""
from __future__ import annotations
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
from urllib.parse import unquote, urlsplit
import uuid
from .atomic import atomic_json, fsync_dir, fsync_tree


def _bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def _hash(value):return hashlib.sha256(_bytes(value)).hexdigest()


def _file_hash(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle, 'sha256').hexdigest()


def _stable(value):
    if isinstance(value, dict):return {k:_stable(v) for k,v in value.items() if k != 'updated_at'}
    if isinstance(value, list):return [_stable(v) for v in value]
    return value


def _vector(value, kind):
    size=384 if kind == 'text' else 512
    if not isinstance(value, list) or len(value) != size or any(isinstance(x, bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in value):
        raise ValueError(f'Invalid {kind} vector; expected {size} finite numbers')
    return value


def _number(value):
    try:return float(value or 0)
    except (TypeError,ValueError):return 0.0


def _documents(catalog):
    """Mirror normalizeCatalog/buildDocuments's sorted, nonblank JS documents."""
    projected=catalog.get('search_projection',{}).get('documents')
    if projected is not None:
        for doc in projected:
            if not doc.get('embed'):continue
            yield {'id':doc['id'],'content':doc['contentId'],'text':doc['text'],
                   'image':doc.get('image','') if doc.get('kind')=='visual' else ''}
        return
    for ai,asset in enumerate(catalog.get('assets', [])):
        aid=str(asset.get('id',asset.get('content_id',ai)))
        content=str(asset.get('content_id',aid))
        highlights=sorted(asset.get('highlights',[]),key=lambda h:_number(h.get('seconds',h.get('start',h.get('time',0)))))
        for i,h in enumerate(highlights):
            text=h.get('note') or h.get('text') or ''
            if text.strip():yield {'id':f'{aid}:visual:{i}','content':content,'text':text,'image':h.get('image_url') or h.get('image') or ''}
        transcript=asset.get('transcript') or asset.get('sentences') or []
        if isinstance(transcript,dict):transcript=transcript.get('sentences',[])
        if not transcript:
            transcript=[{**s,'stream':t.get('stream',t.get('index'))} for t in asset.get('transcripts',[]) for s in (t.get('sentences') or t.get('segments') or [])]
        transcript=sorted((s for s in transcript if (s.get('text') or '').strip()),key=lambda s:_number(s.get('start',s.get('seconds',0))))
        for i,s in enumerate(transcript):
            words=s['text'].strip().split()
            for j in range(0,len(words),85):yield {'id':f'{aid}:speech:{i}:{j//85}','content':content,'text':' '.join(words[j:j+85])}


def _image(notes,url):
    if not isinstance(url,str) or not url.startswith('/notes/') or urlsplit(url).query or urlsplit(url).fragment:raise ValueError('Image must be a local /notes/ URL')
    relative=Path(unquote(url[len('/notes/'):]))
    if relative.is_absolute() or any(p in ('..','.') for p in relative.parts):raise ValueError('Unsafe image path')
    current=notes
    for part in relative.parts:
        current=current/part
        if current.is_symlink():raise ValueError('Image symlinks are not permitted')
    if not current.is_file() or not current.resolve().is_relative_to(notes.resolve()):raise ValueError('Missing or external image')
    return current


@contextmanager
def _cache(notes):
    path=notes/'.search-cache.sqlite'
    if any(Path(str(path)+suffix).is_symlink() for suffix in ('','-wal','-shm')):raise ValueError('Cache files must not be symlinks')
    def connect():
        db=sqlite3.connect(path)
        try:
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':raise sqlite3.DatabaseError('Cache integrity failed')
            db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
            db.execute('CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, kind TEXT NOT NULL, vector TEXT NOT NULL)')
            if [row[1] for row in db.execute('PRAGMA table_info(vectors)')] != ['key','kind','vector']:raise sqlite3.DatabaseError('Invalid cache schema')
            return db
        except BaseException:db.close();raise
    try:db=connect()
    except sqlite3.DatabaseError:
        tag=uuid.uuid4().hex
        for suffix in ('','-wal','-shm'):
            old=Path(str(path)+suffix)
            if old.exists():os.replace(old,notes/(path.name+'.corrupt-'+tag+suffix))
        fsync_dir(notes);db=connect()
    try:yield db
    finally:db.close()


def build(project,catalog,infer,revision):
    """Build/cache vectors and atomically publish one complete catalog pair.

    revision must contain the prepared text, clip and reranker model revisions.
    Returns the vectors payload; read_snapshot returns its matching catalog.
    """
    project=Path(project).resolve();notes=project/'_DIT_NOTES';notes.mkdir(parents=True,exist_ok=True)
    if notes.is_symlink():raise ValueError('Notes root must not be a symlink')
    revision={k:revision[k] for k in ('text','clip','reranker')}
    if any(not isinstance(v,str) or not v for v in revision.values()):raise ValueError('Missing model revision')
    catalog=copy.deepcopy(catalog)
    lock_path=notes/'.search-build.lock'
    if lock_path.is_symlink():raise ValueError('Build lock must not be a symlink')
    with lock_path.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        docs=list(_documents(catalog));items=[];seen=set()
        for doc in docs:
            if doc['id'] in seen:raise ValueError('Duplicate document ID')
            seen.add(doc['id'])
            items.append({'document_id':doc['id'],'kind':'text','value':doc['text'],'key':_hash(['text',revision['text'],doc['content'],doc['text']])})
            if doc.get('image'):
                path=_image(notes,doc['image'])
                items.append({'document_id':doc['id'],'kind':'image','value':path,'key':_hash(['image',revision['clip'],doc['content'],_file_hash(path)])})
        snapshot_revision=_hash({'catalog':_stable(catalog),'revision':revision,'documents':[(i['document_id'],i['kind'],i['key']) for i in items]})
        with _cache(notes) as db:
            found={};missing={'text':{},'image':{}}
            for item in items:
                key=item['key']
                if key in found:continue
                row=db.execute('SELECT kind,vector FROM vectors WHERE key=?',(key,)).fetchone()
                try:
                    if not row or row[0]!=item['kind']:raise ValueError('Cache miss')
                    found[key]=_vector(json.loads(row[1]),item['kind'])
                except (ValueError,TypeError):missing[item['kind']][key]=item
            for kind in ('text','image'):
                pending=list(missing[kind].values())
                for start in range(0,len(pending),8):
                    batch=pending[start:start+8]
                    response=infer('embed_text' if kind=='text' else 'embed_images',[i['value'] for i in batch],'')
                    vectors=response.get('vectors')
                    if not isinstance(vectors,list) or len(vectors)!=len(batch):raise ValueError('Inference returned incorrect vector count')
                    checked=[_vector(v,kind) for v in vectors]
                    with db:
                        for item,vector in zip(batch,checked):
                            db.execute('INSERT OR REPLACE INTO vectors VALUES (?,?,?)',(item['key'],kind,json.dumps(vector,allow_nan=False)))
                            found[item['key']]=vector
            payload={'catalog_revision':snapshot_revision,'revision':revision,'vectors':[{'document_id':i['document_id'],'kind':i['kind'],'vector':found[i['key']]} for i in items]}
        snapshots=notes/'.catalogs';snapshots.mkdir(exist_ok=True)
        if snapshots.is_symlink():raise ValueError('Snapshot root must not be a symlink')
        final=snapshots/snapshot_revision;stage=snapshots/('.stage-'+uuid.uuid4().hex)
        stage.mkdir()
        try:
            atomic_json(stage/'catalog.json',catalog);atomic_json(stage/'vectors.json',payload)
            seal={'catalog_revision':snapshot_revision,'checksums':{n:_file_hash(stage/n) for n in ('catalog.json','vectors.json')}}
            atomic_json(stage/'seal.json',seal);fsync_tree(stage)
            # Rebuilding a corrupt existing revision replaces it only after a full seal.
            existing_valid=False
            if final.is_dir() and not final.is_symlink():
                try:
                    previous=json.loads((final/'seal.json').read_text())
                    existing_valid=previous['catalog_revision']==snapshot_revision and all(not (final/n).is_symlink() and _file_hash(final/n)==previous['checksums'][n] for n in ('catalog.json','vectors.json'))
                except (OSError,ValueError,KeyError,TypeError):pass
            if not existing_valid:
                if final.exists():os.replace(final,snapshots/('.replaced-'+uuid.uuid4().hex))
                os.replace(stage,final);fsync_dir(snapshots)
            atomic_json(notes/'current.json',{'catalog_revision':snapshot_revision,'seal_sha256':_file_hash(final/'seal.json')})
        finally:
            if stage.exists():shutil.rmtree(stage)
        return payload


def read_snapshot(project):
    """Read a checksum-complete sealed pair, or None; never mix generations."""
    notes=Path(project).resolve()/'_DIT_NOTES'
    try:
        if notes.is_symlink():return None
        pointer=json.loads((notes/'current.json').read_text());rev=pointer['catalog_revision']
        if not isinstance(rev,str) or len(rev)!=64 or any(c not in '0123456789abcdef' for c in rev):return None
        folder=notes/'.catalogs'/rev
        if any(p.is_symlink() for p in (notes/'current.json',notes/'.catalogs',folder,folder/'seal.json',folder/'catalog.json',folder/'vectors.json')):return None
        if _file_hash(folder/'seal.json')!=pointer['seal_sha256']:return None
        seal=json.loads((folder/'seal.json').read_text())
        if seal['catalog_revision']!=rev:return None
        for name in ('catalog.json','vectors.json'):
            if _file_hash(folder/name)!=seal['checksums'][name]:return None
        catalog=json.loads((folder/'catalog.json').read_text());vectors=json.loads((folder/'vectors.json').read_text())
        if vectors['catalog_revision']!=rev:return None
        documents=list(_documents(catalog));ids={d['id'] for d in documents};seen=set()
        if any(not isinstance(vectors['revision'].get(k),str) or not vectors['revision'][k] for k in ('text','clip','reranker')):return None
        for entry in vectors['vectors']:
            pair=(entry['document_id'],entry['kind'])
            if pair in seen or pair[0] not in ids or pair[1] not in ('text','image'):return None
            seen.add(pair);_vector(entry['vector'],entry['kind'])
        if {doc for doc,kind in seen if kind=='text'}!=ids:return None
        if {doc for doc,kind in seen if kind=='image'}!={d['id'] for d in documents if d.get('image')}:return None
        return {'catalog':catalog,'vectors':vectors}
    except (OSError,ValueError,TypeError,KeyError,IndexError):return None


import threading
class Snapshots:
    def __init__(self,project):self.project=project;self.signature=None;self.value=None;self.lock=threading.RLock()
    def pair(self):
        from ditnotes.catalog_index import read_snapshot
        p=self.project/'_DIT_NOTES/current.json'
        with self.lock:
            try:s=p.stat();signature=(s.st_ino,s.st_size,s.st_mtime_ns)
            except FileNotFoundError:signature=None
            if signature!=self.signature or self.value is None:
                value=read_snapshot(self.project)
                if value is not None:self.value=value
                self.signature=signature
            return self.value
    def read(self):
        pair=self.pair()
        if pair:return {**pair['catalog'],'catalog_revision':pair['vectors']['catalog_revision']}
        fallback=self.project/'_DIT_NOTES/catalog.json'
        if fallback.is_file():return json.loads(fallback.read_text())
        return {'project':{'id':'waiting-for-ingest','name':'Ingests','updated_at':'initial'},'assets':[]}
    def vectors(self):
        pair=self.pair();return pair['vectors'] if pair else {'revision':{},'vectors':[]}
