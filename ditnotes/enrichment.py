"""Shared durable identity/annotation registry and one Orama search projection."""
from pathlib import Path
import copy,json,time,sqlite3,uuid,os,subprocess
import numpy as np
from .guards import ROOT
from .models import MODELS,speaker_revision
from .diarization import supported_turns
from .project_store import ProjectStore
from .search_projection import project_documents
from .atomic import atomic_json,fsync_dir
from .catalog_index import build,read_snapshot
from .features import features

def store_path(project):return Path(project)/'_DIT_NOTES/project.sqlite3'
def migrate_store(project):
    """SQLite-backup legacy edits; never replace an already-created canonical DB."""
    from .sqlite_safety import require_safe_sqlite
    require_safe_sqlite()
    target=store_path(project);old=Path(project)/'_LAB_NOTES/project.sqlite3'
    if target.exists() or not old.is_file():return target
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name('migration-'+uuid.uuid4().hex+'.sqlite3')
    source=destination=None
    try:
        # Backup API includes committed WAL data; a filesystem copy would not.
        source=sqlite3.connect(old.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
        destination=sqlite3.connect(temporary,timeout=30)
        source.backup(destination);destination.close();destination=None
        source.close();source=None
        with temporary.open('rb') as handle:os.fsync(handle.fileno())
        try:
            # Atomic no-replace publication also protects against another process
            # creating a canonical DB or saving its first edit during this backup.
            os.link(temporary,target)
        except FileExistsError:pass
        fsync_dir(target.parent)
    finally:
        if destination is not None:destination.close()
        if source is not None:source.close()
        temporary.unlink(missing_ok=True);fsync_dir(target.parent)
    return target

def register_voices(store,content,result):
    assignments=[]
    for track in result.get('tracks',[]):
        diar=track.get('diarization',{})
        raw=diar.get('raw_turns',diar.get('turns',[]));diar['raw_turns']=copy.deepcopy(raw)
        diar['turns']=supported_turns(raw,track.get('sentences',[]),result['duration'])
        supported_locals={t['local_speaker'] for t in diar['turns']}
        prefix=f'stream-{track["stream_index"]}:diar-{MODELS["diarization"]["revision"][:12]}:'
        by_local={};overlaps={}
        for turn in diar.get('turns',[]):
            local=turn['local_speaker'];overlaps.setdefault(local,set())
            for other in diar.get('turns',[]):
                if other['local_speaker']!=local and min(turn['end'],other['end'])>max(turn['start'],other['start']):overlaps[local].add(other['local_speaker'])
        for local in diar.get('local_speakers',[]):
            if local['local_speaker'] not in supported_locals:continue
            key=prefix+local['local_speaker']
            excluded=[by_local[x] for x in overlaps.get(local['local_speaker'],()) if x in by_local]
            # One enrollment vector per clean window; centroid pooling above is bounded,
            # and no turn-only records inflate the voice profile.
            windows=local['enrollment_windows'][:1]
            for window in windows:
                row=store.assign_speaker(content,key,window['start'],window['end'],local['embedding'],local['model_revision'],local['quality'],
                        quality_components=local['quality_components'],auto_assign=features()['automatic_voice_grouping'],exclude_person_ids=excluded,overlap_group=f'audio-stream-{track["stream_index"]}',calibration_id=None,
                        match_threshold=.82,margin=.08)
                by_local[local['local_speaker']]=row['person_id'];assignments.append(row)
        for turn in diar.get('turns',[]):
            key=prefix+turn['local_speaker']
            row=store.record_turn(content,key,turn['start'],turn['end'],model_revision=diar.get('speaker_model_revision',speaker_revision()),overlap=turn['overlap'],overlap_group=f'audio-stream-{track["stream_index"]}')
            by_local.setdefault(turn['local_speaker'],row['person_id'])
        for token in diar.get('token_speakers',[]):
            token['person_id']=by_local.get(token.get('local_speaker'))
            token['person_candidates']=[by_local[x] for x in token.get('speaker_candidates',[]) if x in by_local]
        track['speaker_assignments']=[{'local_speaker':local,'person_id':person,'identity_basis':'voice'} for local,person in sorted(by_local.items())]
    return assignments

def register_result(project,identity,content,result,profile):
    """Idempotently derive project identities from sealed AI evidence."""
    with ProjectStore(migrate_store(project),project_id=identity['id']) as store:
        working=copy.deepcopy(result);voices=register_voices(store,content,working)
        faces=[];frame_ids={};prefix='/notes/.objects/'+content+'/'+profile+'/'
        for row in result.get('faces',{}).get('observations',[]):
            observed=store.assign_face(content,row['seconds'],row['embedding'],row['model_revision'],row['quality'],
                bbox=row['bbox'],frame_ref=prefix+row['frame'],crop_ref=prefix+row['crop'],detection_id=row['detection_id'],
                quality_components=row['quality_components'],auto_assign=features()['automatic_face_grouping'],exclude_face_ids=frame_ids.get(row['seconds'],[]))
            frame_ids.setdefault(row['seconds'],[]).append(observed['face_id']);faces.append(observed)
        atomic_json(Path(project)/'_DIT_NOTES'/f'{content}-identity-alignment.json',{'content_id':content,'profile_id':profile,'tracks':working.get('tracks',[]),'voices':voices,'faces':faces})
        return {'voices':len(voices),'faces':len(faces)}

def _links(project,catalog,payload,store,revision):
    notes=Path(project)/'_DIT_NOTES';summaries={}
    for asset in catalog.get('assets',[]):
        vectors=[r['vector'] for r in payload['vectors'] if r['kind']=='image' and r['document_id'].startswith(asset['id']+':visual:')]
        if vectors:
            mean=np.mean(np.asarray(vectors,dtype=np.float64),axis=0);norm=np.linalg.norm(mean)
            if norm>1e-10:summaries[asset['content_id']]={'vector':(mean/norm).tolist(),'model_revision':revision['clip']+':mean-sampled-l2-v1'}
    atomic_json(notes/'clip-fingerprints.json',summaries)
    annotated=sorted({a['content_id'] for a in store.annotations() if a['source']=='operator'})
    if not annotated:return 0,0
    count=0;inherited=0
    for content,packet in summaries.items():
        eligible=[x for x in annotated if x!=content]
        if not eligible:continue
        result=subprocess.run([str(ROOT/'bin/node'),str(ROOT/'search/link-candidates.mjs'),'--project',str(project),'--content-id',content,'--eligible',json.dumps(eligible),'--limit','3','--threshold','.9'],capture_output=True,text=True,timeout=30,check=True)
        candidates=json.loads(result.stdout)['candidates'];bounded={r['content_id']:{'vector':r['vector'],'model_revision':r['model_revision']} for r in candidates}
        count+=len(store.suggest_links(content,packet['vector'],bounded,packet['model_revision'],threshold=.9))
        if features()['automatic_note_inheritance'] and candidates:
            ranked=sorted(candidates,key=lambda r:-r['score'] if 'score' in r else -r.get('cosine',0))
            # Native search reports CLIP cosine. Only a near-identical, distinct
            # best source is eligible; inherited notes never become new sources.
            scores={r['content_id']:float(r.get('cosine',r.get('score',0))) for r in ranked}
            eligible_links=store.links(content_id=content,status='suggested')
            best=sorted(scores,key=scores.get,reverse=True)
            if best and scores[best[0]]>=.97 and (len(best)<2 or scores[best[0]]-scores[best[1]]>=.05):
                for link in eligible_links:
                    if link['from_content']==best[0]:store.accept_link(link['id'],automatic=True);inherited+=1
    return count,inherited

def _publish(project,backend):
    from .library import _lock,_read
    project=Path(project);notes=project/'_DIT_NOTES'
    with _lock(notes):
        catalog=_read(notes/'catalog.json',{})
        if not catalog:return {'ready':False,'reason':'No catalog yet'}
        with ProjectStore(migrate_store(project),project_id=catalog['project']['id']) as store:
            from .identity_grouping import regroup
            grouping=regroup(store)
            # Capture one SQLite WAL read snapshot without blocking operator writes.
            store.db.execute('BEGIN')
            try:catalog['search_projection']=project_documents(catalog,store);edit_revision=store.edit_revision
            finally:store.db.commit()
            ready=backend.readiness()
            if not ready['ready']:raise RuntimeError('Offline search models are not prepared')
            payload=build(project,catalog,backend._infer,ready['revision'])
            snapshot=read_snapshot(project)
            if not snapshot or snapshot['catalog'].get('search_projection',{}).get('edit_revision')!=edit_revision:raise RuntimeError('Search snapshot failed edit revision verification')
            atomic_json(notes/'catalog.json',catalog)
            links,inherited=_links(project,catalog,payload,store,ready['revision'])
            if inherited:
                store.db.execute('BEGIN')
                try:catalog['search_projection']=project_documents(catalog,store);edit_revision=store.edit_revision
                finally:store.db.commit()
                payload=build(project,catalog,backend._infer,ready['revision']);atomic_json(notes/'catalog.json',catalog)
            store.mark_indexed(edit_revision)
            return {'ready':True,'edit_revision':edit_revision,'indexed_edit_revision':store.indexed_edit_revision,'vectors':len(payload['vectors']),'suggestions':links,'grouping':grouping}

def publish_index(project,backend):
    """Own dispatch to the existing serialized MLX executor; caller is non-executor thread."""
    return backend.executor.submit(_publish,Path(project),backend).result(timeout=900)
