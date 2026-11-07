#!/usr/bin/env python3
"""Fieldnotes: offline model setup, folder analysis and local browsing."""
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
os.environ['PATH']=str(ROOT/'bin')+':'+os.environ.get('PATH','/usr/bin:/bin')
from ditnotes.model_roles import MODEL_LOCK, MODEL_ROLES, ANALYSIS_MODELS, CHAT_MODEL



def _weight_complete(path):
    try:
        with path.open('rb') as f:
            length=int.from_bytes(f.read(8),'little')
            if not 0<length<100_000_000:return False
            header=json.loads(f.read(length))
        end=max(v['data_offsets'][1] for k,v in header.items() if k!='__metadata__')
        return path.stat().st_size>=8+length+end
    except (OSError,ValueError,KeyError,TypeError):return False


def model_readiness(root):
    result={}
    for name in MODEL_LOCK:
        folder=Path(root)/'models'/name;errors=[]
        required=['config.json','tokenizer.model'] if name=='parakeet' else ['config.json','tokenizer.json','tokenizer_config.json','preprocessor_config.json']
        for filename in required:
            path=folder/filename
            if not path.is_file() or path.stat().st_size==0:errors.append(filename+' missing/empty')
            elif filename.endswith('.json'):
                try:json.loads(path.read_text())
                except ValueError:errors.append(filename+' invalid JSON')
        index=folder/'model.safetensors.index.json'
        try:
            weights=sorted(set(json.loads(index.read_text())['weight_map'].values())) if index.exists() else ['model.safetensors']
        except (ValueError,KeyError):weights=[];errors.append('invalid weight index')
        if not weights:errors.append('no weight shards declared')
        for weight in weights:
            if Path(weight).is_absolute() or '..' in Path(weight).parts or not _weight_complete(folder/weight):errors.append(weight+' missing/truncated')
        result[name]={'ready':not errors,'errors':errors,'repository':MODEL_LOCK[name][0],'revision':MODEL_LOCK[name][1]}
    return result


def prepare_offline(check_only=False):
    import prepare_search,prepare_mlx_text,prepare_mlx_clip
    from ditnotes.sqlite_safety import readiness as sqlite_readiness
    sqlite_status=sqlite_readiness()
    status=model_readiness(ROOT)
    if not check_only:
        from huggingface_hub import snapshot_download
        for name,item in status.items():
            if item['ready']:continue
            repo,revision=MODEL_LOCK[name]
            print('Preparing local model:',name,flush=True)
            lock=json.loads((ROOT/'deploy/assets.lock.json').read_text())
            prefix=name+'/'
            allowed=[row['path'][len(prefix):] for row in lock['model_files'] if row['path'].startswith(prefix) and not row.get('generated')]
            if not allowed:raise RuntimeError('Missing pinned model download inventory: '+name)
            snapshot_download(repo,revision=revision,local_dir=ROOT/'models'/name,max_workers=1,allow_patterns=allowed)
            (ROOT/'models'/name/'provenance.json').write_text(json.dumps({'repo':repo,'revision':revision},indent=2)+'\n')
        status=model_readiness(ROOT)
        search=prepare_search.prepare(ROOT)
    else:search=prepare_search.check(ROOT,write=False)
    mlx_text=prepare_mlx_text.check(ROOT,write=False) if check_only else prepare_mlx_text.prepare(ROOT)
    mlx_clip=prepare_mlx_clip.check(ROOT,write=False) if check_only else prepare_mlx_clip.prepare(ROOT)
    from ditnotes.models import check as voice_check,prepare as voice_prepare
    from ditnotes.face_models import check as face_check,prepare as face_prepare
    voice=voice_check(ROOT) if check_only else voice_prepare(ROOT)
    face=face_check() if check_only else face_prepare()
    native=(ROOT/'ditnotes/native/feature_select').is_file() and os.access(ROOT/'ditnotes/native/feature_select',os.X_OK)
    viewer=(ROOT/'viewer/dist/index.html').is_file()
    result={'ready':sqlite_status['ready'] and all(m['ready'] for m in status.values()) and search['ready'] and mlx_text['ready'] and mlx_clip['ready'] and native and viewer and voice['ready'] and face['ready'],
            'sqlite':sqlite_status,'identities':{'voice':voice,'face':face},'analysis_models':{name:status[name] for name in ANALYSIS_MODELS},'chat_models':{CHAT_MODEL:status[CHAT_MODEL]},'model_roles':MODEL_ROLES,'search':search,'mlx_search':{'text':mlx_text,'clip':mlx_clip},'native_selector_ready':native,'viewer_ready':viewer,
            'note':'File completeness checked; run a test clip to validate inference on this Mac.'}
    if not check_only:
        from ditnotes.library import _save
        _save(ROOT/'runtime/offline-readiness.json',result)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    setup=commands.add_parser('prepare-offline',help='Download missing pinned models and browser search assets once');setup.add_argument('--check',action='store_true',help='Read-only local readiness check; no downloads')
    process=commands.add_parser('process',help='Analyze one file or a folder; resume and recognize reorganized files')
    process.add_argument('input',type=Path);process.add_argument('--project',type=Path);process.add_argument('--models-root',type=Path,default=ROOT/'models')
    process.add_argument('--interval',type=float,default=2);process.add_argument('--max-frames',type=int,default=12);process.add_argument('--timeout',type=float,default=300)
    face=commands.add_parser('tune-faces',help='Plan or apply face-only backfill and regrouping; retain audio/captions and operator edits')
    face.add_argument('project',type=Path);face.add_argument('--run',action='store_true')
    serve=commands.add_parser('serve',help='Browse a processed project on localhost');serve.add_argument('project',type=Path);serve.add_argument('--port',type=int,default=8766)
    args=parser.parse_args(argv)
    if args.command=='prepare-offline':
        status=prepare_offline(args.check);print(json.dumps(status,indent=2));return 0 if status['ready'] else 1
    if args.command!='prepare-offline':
        from ditnotes.sqlite_safety import require_safe_sqlite
        require_safe_sqlite()
    if args.command!='prepare-offline':os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
    if args.command=='serve':
        from ditnotes.server import serve
        serve(args.project,args.port,tool_root=ROOT);return 0
    if args.command=='tune-faces':
        from ditnotes.face_maintenance import plan,run
        if not args.run:
            result=plan(args.project);result.pop('frames',None);print(json.dumps(result,indent=2));return 0
        from ditnotes.search_backend import SearchBackend
        from ditnotes.enrichment import publish_index
        from ditnotes.project_retry import retry_project
        backend=SearchBackend(ROOT,lambda x:None)
        try:result=retry_project(lambda:run(args.project,publisher=lambda project:retry_project(lambda:publish_index(project,backend,projection_only=True))))
        finally:backend.close()
        print(json.dumps(result,indent=2));return 0
    from ditnotes.library import process
    from ditnotes.project_retry import retry_project
    result=retry_project(lambda:process(args.input,args.project,models_root=args.models_root,
                   options={'interval':args.interval,'max_frames':args.max_frames,'timeout':args.timeout},
                   progress=lambda path,status:print(f'{path}: {status}',file=sys.stderr,flush=True)))
    from ditnotes.search_backend import SearchBackend
    from ditnotes.enrichment import publish_index
    backend=SearchBackend(ROOT,lambda x:None)
    try:result['index']=retry_project(lambda:publish_index(Path(result['project']),backend))
    finally:backend.close()
    print(json.dumps(result,indent=2));return 1 if result['counts']['failed'] else 0

if __name__=='__main__':raise SystemExit(main())
