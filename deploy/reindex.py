"""Plan/resume analysis upgrades over a project's previously registered scopes."""
from __future__ import annotations
import argparse,json,os,sqlite3,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def scopes(project):
    from ditnotes.guards import project_path
    project=project_path(project);notes=project/'_DIT_NOTES'
    if notes.is_symlink():raise ValueError('Notes directory must not be a symlink')
    identity=json.loads((notes/'project.json').read_text())
    values=identity.get('ingest_paths')
    if not isinstance(values,list) or not values:raise ValueError('No registered ingest scopes; refusing an unrestricted scan')
    paths=[]
    for value in values:
        p=Path(value)
        if p.is_absolute() or '..' in p.parts:raise ValueError('Registered scope escapes project')
        full=project/p
        if not full.exists() or full.is_symlink() or not full.resolve().is_relative_to(project):raise ValueError('Registered scope missing or unsafe: '+value)
        paths.append(full)
    # Parent scopes cover children; processing duplicated content remains cached as well.
    return project,[p for p in paths if not any(p!=other and p.is_relative_to(other) for other in paths)]

def plan(project):
    from ditnotes.library import discover,profile_id,_valid_object,_sha,_stat
    project,paths=scopes(project);notes=project/'_DIT_NOTES'
    state=json.loads((notes/'state.json').read_text()) if (notes/'state.json').exists() else {'paths':{}}
    profile=profile_id();rows=[]
    for path in sorted({p for scope in paths for p in discover(scope,project)}):
        rel=path.relative_to(project).as_posix();old=state.get('paths',{}).get(rel,{})
        content=old.get('sha256') if old.get('stat')==_stat(path) else None
        if not content:content=_sha(path)
        complete=_valid_object(notes/'.objects'/content/profile,content,profile)
        rows.append({'path':rel,'content_id':content,'previous_profile':old.get('profile_id'),'profile':profile,'action':'reuse' if complete else 'analyze'})
    return {'project':str(project),'scopes':[str(p.relative_to(project)) for p in paths],'profile':profile,'files':len(rows),'analyze':sum(r['action']=='analyze' for r in rows),'reuse':sum(r['action']=='reuse' for r in rows),'rows':rows}

def backup_operator_db(project):
    from ditnotes.atomic import fsync_dir
    db=project/'_DIT_NOTES/project.sqlite3'
    if not db.is_file():return None
    if db.is_symlink():raise ValueError('Operator database cannot be a symlink')
    target=project/'_DIT_NOTES/backups'/('before-reindex-'+str(time.time_ns())+'.sqlite3');target.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(target) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Operator backup failed integrity check')
    with target.open('rb') as f:os.fsync(f.fileno())
    fsync_dir(target.parent);return str(target)

def execute(project):
    # No force/delete: the existing content/profile seals decide work remaining.
    from ditnotes.sqlite_safety import require_safe_sqlite
    require_safe_sqlite()
    from ditnotes.engine import Engine
    from ditnotes.library import process
    from ditnotes.search_backend import SearchBackend
    from ditnotes.enrichment import publish_index
    before=plan(project);project,paths=scopes(project);backup=backup_operator_db(project)
    class DeferredEngine:
        """A search/UI refresh with sealed analysis never loads ASR/VLM models."""
        def __init__(self):self.engine=None;self.progress_callback=None
        def analyze(self,path,output):
            if self.engine is None:self.engine=Engine(models_root=ROOT/'models')
            self.engine.progress_callback=self.progress_callback
            return self.engine.analyze(path,output)
        def close(self):
            if self.engine is not None:self.engine.close()
    engine=DeferredEngine();totals={'processed':0,'reused':0,'failed':0,'files':0}
    try:
        for scope in paths:
            result=process(scope,project,models_root=ROOT/'models',engine=engine,progress=lambda p,s:print(p+': '+s,file=sys.stderr,flush=True))
            for key in totals:totals[key]+=result['counts'][key]
    finally:engine.close()
    backend=SearchBackend(ROOT,lambda x:None)
    try:index=publish_index(project,backend)
    finally:backend.close()
    return {'plan':before,'counts':totals,'index':index,'operator_backup':backup,'remaining':plan(project)['analyze']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--run',action='store_true');a=p.parse_args()
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',PATH=str(ROOT/'bin')+':'+os.environ.get('PATH','/usr/bin:/bin'))
    result=execute(a.project) if a.run else plan(a.project);print(json.dumps(result,indent=2))
    return 1 if result.get('counts',{}).get('failed') else 0
if __name__=='__main__':raise SystemExit(main())
