#!/usr/bin/env python3
"""Real local A→caption-upgrade/interruption→UI-only-upgrade playtest.

Requires an already verified runtime fixture to seed immutable models/FFmpeg.
Everything else is built by the real deployment scripts in a disposable home.
No host apps, production configuration or source media are modified. Results and
extracted media stay outside the checkout. This is not a substitute for a clean
machine first-install test; cached dependencies and validated model assets are reused.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, shutil, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def blocks(text):
    decoder=json.JSONDecoder();values=[]
    for match in re.finditer(r'(?m)^\{',text):
        try:value,_=decoder.raw_decode(text[match.start():]);values.append(value)
        except ValueError:pass
    return values


class Playtest:
    def __init__(self,args):
        self.args=args;self.source=args.source.resolve();self.fixture=args.fixture.resolve();self.home=args.home.resolve()
        self.project=self.home.parent/(self.home.name+'-project');self.logs=self.home.parent/(self.home.name+'-evidence')
        self.sources=self.home.parent/(self.home.name+'-sources')
        for path in [self.logs,self.sources]:path.mkdir(parents=True,exist_ok=True)
        if self.project.exists() or (self.home/'current').exists():raise RuntimeError('Use a new disposable --home; existing project/current is not overwritten')
        self.manager=module(self.source/'deploy/manager.py','playtest_manager')
        self.report={'home':str(self.home),'project':str(self.project),'started_at':time.time(),'stages':{},'optimizations':['Immutable SHA-verified model assets seeded from a prior local fixture','Previously source-built FFmpeg reused after SHA comparison; fresh venv/npm/native builds per release','No originals or live host apps/settings touched']}
        self.env=dict(os.environ,FIELD_LAB_CACHE=str(args.cache.resolve()))
    def note(self,text):print(text,flush=True)
    def save(self):
        path=self.logs/'report.json';temp=path.with_suffix('.tmp');temp.write_text(json.dumps(self.report,indent=2)+'\n');temp.replace(path)
    def run(self,name,args,cwd=None,timeout=1200):
        self.note(name);path=self.logs/(name+'.log');start=time.monotonic()
        with path.open('w') as output:
            completed=subprocess.run(list(map(str,args)),cwd=cwd,env=self.env,stdout=output,stderr=subprocess.STDOUT,timeout=timeout)
        if completed.returncode:raise RuntimeError(name+' failed; inspect '+str(path))
        return {'elapsed_seconds':round(time.monotonic()-start,3),'log':str(path),'json':blocks(path.read_text())}
    def snapshot(self,label,previous=None):
        dest=self.sources/label
        if dest.exists():raise RuntimeError('Source snapshot already exists: '+str(dest))
        origin=previous or self.source
        for name in self.manager.source_files(origin):
            target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin/name,target)
        return dest
    def seed(self,release):
        lock=json.loads((release/'deploy/assets.lock.json').read_text())
        for row in lock['model_files']:
            source=self.fixture/'models'/row['path'];target=release/'models'/row['path']
            if source.stat().st_size!=row['bytes'] or digest(source)!=row['sha256']:raise RuntimeError('Seed model hash differs: '+row['path'])
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():os.link(source,target)
        for name,value in lock['model_json'].items():
            target=release/'models'/name;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.write_text(json.dumps(value,indent=2)+'\n')
        for name in ['ffmpeg','ffprobe']:
            source=self.fixture/'tools/ffmpeg/bin'/name;target=release/'tools/ffmpeg/bin'/name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            assert digest(source)==digest(target)
    def deploy(self,label,source):
        self.run(label+'-git-init',['git','init',source])
        self.run(label+'-git-add',['git','-C',source,'add','--all'])
        self.run(label+'-git-commit',['git','-C',source,'-c','user.name=Field Lab playtest','-c','user.email=playtest@localhost','commit','-m','Disposable '+label+' source snapshot'])
        candidate=self.manager.stage(source,self.home);release=Path(candidate['release']);self.seed(release)
        info=self.run(label+'-prepare',[sys.executable,source/'deploy/field.py','install' if label=='A' else 'update','--source',source,'--home',self.home])
        info['activate']=self.run(label+'-activate',[sys.executable,source/'deploy/field.py','activate','--home',self.home,'--release',release.name,'--offshoot-idle'])
        info['release']=str(release);info['release_id']=release.name
        assert (self.home/'current').resolve()==release
        self.report['stages'][label]=info;self.save();return release
    def plan(self,release):
        info=self.run('plan-'+str(time.time_ns()),[release/'.venv/bin/python',release/'deploy/reindex.py','--project',self.project])
        return next(value for value in info['json'] if 'analyze' in value)
    def metadata(self,release,write=False):
        code='''import json,sys
from pathlib import Path
from ditnotes.project_store import ProjectStore
project=Path(sys.argv[1]);identity=json.loads((project/'_DIT_NOTES/project.json').read_text())
with ProjectStore(project/'_DIT_NOTES/project.sqlite3',identity['id']) as store:
 if sys.argv[2]=='write':
  import sqlite3,time
  content=json.loads((project/'_DIT_NOTES/catalog.json').read_text())['assets'][0]['content_id']
  store.add_annotation(content,'Playtest operator note: retain through upgrades',metadata={'playtest':True})
  faces=[x for x in store.faces() if not x['merged_into']]
  voices=[x for x in store.people() if not x['merged_into']]
  assert faces and voices,(len(faces),len(voices))
  store.name_face(faces[0]['id'],'Playtest face');store.name_person(voices[0]['id'],'Playtest voice')
 result={'annotations':store.annotations(),'faces':[x for x in store.faces() if x['name']],'people':[x for x in store.people() if x['name']]}
 print(json.dumps(result))
'''
        result=self.run('metadata-'+str(time.time_ns()),[release/'.venv/bin/python','-c',code,self.project,'write' if write else 'read'],cwd=release)
        return result['json'][-1]
    def queues(self,release,write=False):
        code='''import json,time,sys
from ingest_service import config,connect
with connect(config()) as db:
 if sys.argv[1]=='write':db.execute("INSERT INTO jobs(job_id,state,payload,enqueued_at,attempts) VALUES(?,?,?,?,?)",('upgrade-playtest','done','{}',1.0,1))
 print(json.dumps([dict(x) for x in db.execute('SELECT * FROM jobs ORDER BY job_id')]))
'''
        info=self.run('queue-'+str(time.time_ns()),[release/'.venv/bin/python','-c',code,'write' if write else 'read'],cwd=release)
        # Top-level list is parsed separately because log JSON helper collects objects.
        return json.loads(Path(info['log']).read_text().strip())
    def media_hashes(self):return {p.name:digest(p) for p in sorted((self.project/'media').glob('*.mp4'))}
    def main(self):
        original_hash=digest(self.args.trailer);self.project.mkdir(parents=True);(self.project/'media').mkdir()
        ffmpeg=self.fixture/'bin/ffmpeg'
        for n,start in enumerate([0,52],1):
            self.run('extract-'+str(n),[ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-ss',start,'-i',self.args.trailer,'-t',22,'-vf','scale=960:-2','-c:v','h264_videotoolbox','-b:v','2500k','-c:a','aac',self.project/'media'/('sample-'+str(n)+'.mp4')])
        media=self.media_hashes();sourceA=self.snapshot('A');a=self.deploy('A',sourceA)
        # Config is test-only and never passed to OffShoot or start; stop/backup require no mounted volume check.
        config={'volume_mount':str(self.project.parent),'ingest_root':str(self.project),'ingest_folder':self.project.name,'volume_uuid':'PLAYTEST-NOT-A-REAL-VOLUME','port':self.args.port}
        (self.home/'shared/config.json').write_text(json.dumps(config,indent=2)+'\n')
        queues=self.queues(a,True)
        self.report['A_processing']=self.run('A-process',[a/'.venv/bin/python',a/'dit_notes.py','process',self.project/'media','--project',self.project])
        planA=self.plan(a);assert planA['files']==2 and planA['analyze']==0,planA
        metadata=self.metadata(a,True);self.report['metadata_before']=metadata;self.report['plan_A']=planA;self.save()
        sourceB=self.snapshot('B',sourceA);prompt=sourceB/'ditnotes/prompts/field-caption.txt'
        prompt.write_text('Write one concise 4–8-word footage-search phrase naming the main visible subject and the distinctive surroundings or object. Describe only visible evidence. Do not infer motion, occupation, intention, species or material when unclear. Prefer broad nouns for uncertain details. Avoid mood and lighting prose. Output one plain phrase only. Empty frame: BLACK.\n')
        b=self.deploy('B',sourceB);planB=self.plan(b);assert planB['analyze']==2 and planB['profile']!=planA['profile'],planB
        log=self.logs/'B-interrupted.log';self.note('B real reindex: interrupt after first complete object')
        with log.open('w') as output:
            child=subprocess.Popen([str(sys.executable),str(sourceB/'deploy/field.py'),'reindex','--home',str(self.home),'--project',str(self.project),'--run','--offshoot-idle'],env=self.env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+600;first=None
            while child.poll() is None and time.monotonic()<deadline:
                seals=list((self.project/'_DIT_NOTES/.objects').glob('*/'+planB['profile']+'/complete.json'))
                if seals:first=seals;os.killpg(child.pid,signal.SIGTERM);break
                time.sleep(.02)
            if first is None:
                if child.poll() is None:os.killpg(child.pid,signal.SIGKILL)
                child.wait();raise RuntimeError('No first B object observed before interruption; '+str(log))
            try:child.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        partial=self.plan(b);assert partial['reuse']==1 and partial['analyze']==1,partial
        self.report['B_interrupted']={'exit_code':child.returncode,'first_objects':[str(x) for x in first],'plan_after_interrupt':partial,'log':str(log)}
        resumed=self.run('B-resume',[sys.executable,sourceB/'deploy/field.py','reindex','--home',self.home,'--project',self.project,'--run','--offshoot-idle'])
        resume=next(x for x in resumed['json'] if 'counts' in x);assert resume['counts']['reused']==1 and resume['counts']['processed']==1 and resume['remaining']==0,resume
        self.report['B_resumed']=resume;assert self.metadata(b)==metadata;assert self.queues(b)==queues;assert self.media_hashes()==media;self.save()
        sourceC=self.snapshot('C',sourceB);jsx=sourceC/'viewer/src/main.jsx';text=jsx.read_text();assert '>Images</button>' in text;jsx.write_text(text.replace('>Images</button>','>Stills</button>',1))
        c=self.deploy('C',sourceC);planC=self.plan(c);assert planC['profile']==planB['profile'] and planC['analyze']==0 and planC['reuse']==2,planC
        before_seals={str(p.relative_to(self.project)):digest(p) for p in (self.project/'_DIT_NOTES/.objects').glob('*/*/complete.json')}
        self.report['C_reindex']=self.run('C-reindex',[sys.executable,sourceC/'deploy/field.py','reindex','--home',self.home,'--project',self.project,'--run','--offshoot-idle'])
        cresult=next(x for x in self.report['C_reindex']['json'] if 'counts' in x);assert cresult['counts']['processed']==0 and cresult['counts']['reused']==2,cresult
        after_seals={str(p.relative_to(self.project)):digest(p) for p in (self.project/'_DIT_NOTES/.objects').glob('*/*/complete.json')};assert before_seals==after_seals
        self.report['plan_C']=planC;assert self.metadata(c)==metadata;assert self.queues(c)==queues;assert self.media_hashes()==media;assert digest(self.args.trailer)==original_hash
        with socket.socket() as sock:sock.bind(('127.0.0.1',self.args.port))
        server_log=(self.logs/'C-server.log').open('w')
        server=subprocess.Popen([str(c/'.venv/bin/python'),str(c/'dit_notes.py'),'serve',str(self.project),'--port',str(self.args.port)],stdout=server_log,stderr=subprocess.STDOUT,env=self.env,start_new_session=True)
        base='http://127.0.0.1:'+str(self.args.port)
        deadline=time.monotonic()+60
        while True:
            try:
                with urllib.request.urlopen(base+'/',timeout=3) as response:html=response.read().decode()
                break
            except Exception:
                if server.poll() is not None or time.monotonic()>deadline:raise RuntimeError('C UI did not start; inspect C-server.log')
                time.sleep(.2)
        script=re.search(r'<script[^>]+src="([^"]+)"',html).group(1)
        with urllib.request.urlopen(base+script,timeout=5) as response:bundle=response.read()
        assert b'Stills' in bundle
        old_html=(b/'viewer/dist/index.html').read_text();old_script=re.search(r'<script[^>]+src="([^"]+)"',old_html).group(1)
        assert old_script!=script
        self.report.update(ready=True,finished_at=time.time(),source_media_hashes_unchanged=True,operator_metadata_preserved=True,queue_preserved=True,ui={'url':base,'pid':server.pid,'new_bundle':script,'old_bundle':old_script,'new_label':'Stills','served_bundle_sha256':hashlib.sha256(bundle).hexdigest()},source_hash_before=original_hash,source_hash_after=digest(self.args.trailer))
        self.save();self.note(json.dumps({'ready':True,'report':str(self.logs/'report.json'),'ui':base},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--fixture',type=Path,required=True);parser.add_argument('--media','--trailer',dest='trailer',type=Path,required=True);parser.add_argument('--home',type=Path,default=Path('/tmp/field-lab-upgrade-playtest'));parser.add_argument('--cache',type=Path,default=Path.home()/'Library/Caches/Field Lab');parser.add_argument('--port',type=int,default=18796)
    args=parser.parse_args();test=Playtest(args)
    try:test.main()
    except BaseException as error:test.report.update(ready=False,error=repr(error));test.save();raise
if __name__=='__main__':main()
