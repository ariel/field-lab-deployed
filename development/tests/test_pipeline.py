from pathlib import Path
from types import SimpleNamespace
import json,math,queue,tempfile,time,unittest
from PIL import Image
from lab_indexer.guards import ROOT,PRODUCTION
from lab_indexer.models import speaker_revision
from lab_indexer.pipeline import Pipeline
from lab_indexer.engine import _Worker
class FakeEngine:
    calls=0
    def analyze(self,source,output):
        self.calls+=1;output=Path(output);(output/'frames').mkdir();Image.new('RGB',(8,8)).save(output/'frames/0.jpg')
        result={'status':'complete','duration':10,'probe':{'streams':[{'codec_type':'video','width':8,'height':8}]},'highlights':[{'seconds':1,'label':'Trees','frame':'frames/0.jpg'}],
                'tracks':[{'stream_index':1,'sentences':[{'start':0,'end':4,'text':'Hello world'}], 'diarization':{'speaker_model_revision':speaker_revision(),'turns':[{'start':0,'end':4,'local_speaker':'0','overlap':False}],
                'local_speakers':[{'local_speaker':'0','embedding':[1.]+[0.]*191,'model_revision':speaker_revision(),'quality':1,'quality_components':{},'enrollment_windows':[{'start':0,'end':4}]}],
                'token_speakers':[{'start':1,'end':2,'text':'Hello','local_speaker':'0','speaker_candidates':['0']} ]}}],'timing':{'total_seconds':0.01}}
        (output/'result.json').write_text(json.dumps(result));return result
    def close(self):pass
class PipelineTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'projects').mkdir(exist_ok=True);self.temp=tempfile.TemporaryDirectory(dir=ROOT/'projects');self.root=Path(self.temp.name);self.source=self.root/'input.mp4';self.source.write_bytes(b'fake media');self.engine=FakeEngine();self.infer=[]
    def tearDown(self):self.temp.cleanup()
    def pipeline(self):
        p=Pipeline(self.root/'project',engine=self.engine)
        def infer(action,values,query=''):
            self.infer.append((action,len(values)));dim=384 if action=='embed_text' else 512;return {'vectors':[[1/math.sqrt(dim)]*dim for _ in values]}
        p._infer=infer;return p
    def test_full_pipeline_cache_and_operator_edits(self):
        with self.pipeline() as p:
            a=p.analyze(self.source);self.assertFalse(a['analysis_reused']);self.assertEqual(self.engine.calls,1);self.assertTrue(self.infer)
            self.infer.clear();b=p.analyze(self.source);self.assertTrue(b['analysis_reused']);self.assertFalse(self.infer);self.assertEqual(self.engine.calls,1)
            from lab_indexer.project_store import ProjectStore
            with ProjectStore(p.project/'_LAB_NOTES/project.sqlite3') as store:
                person=store.people()[0]['id'];store.name_person(person,'Ariel');store.add_annotation(a['content_id'],'Excellent sound',metadata={'tag':'interview'})
            p.index();self.assertTrue(self.infer)
            catalog=json.loads((p.project/'catalog.json').read_text());docs=catalog['search_projection']['documents']
            self.assertTrue(any(d['source']=='operator' and 'Excellent sound' in d['text'] for d in docs));self.assertTrue(any('Ariel' in d['personNames'] for d in docs))
        self.assertEqual(self.source.read_bytes(),b'fake media')
    def test_similar_clip_suggests_but_never_silently_inherits(self):
        from lab_indexer.project_store import ProjectStore
        with self.pipeline() as p:
            first=p.analyze(self.source)
            with ProjectStore(p.project/'_LAB_NOTES/project.sqlite3') as store:store.add_annotation(first['content_id'],'Prairie exterior',metadata={'location':'test'})
            other=self.root/'other.mp4';other.write_bytes(b'new fake container')
            second=p.analyze(other)
            self.assertGreater(second['metadata_links']['count'],0)
            with ProjectStore(p.project/'_LAB_NOTES/project.sqlite3') as store:
                self.assertFalse(store.annotations(second['content_id']))
                links=store.links(second['content_id']);self.assertEqual(links[0]['status'],'suggested')
                store.accept_link(links[0]['id']);inherited=store.annotations(second['content_id'])[0]
                self.assertEqual(inherited['source'],'accepted_inheritance')
                self.assertEqual(inherited['metadata']['source_content_id'],first['content_id'])
                self.assertEqual(len(store.annotations(first['content_id'])),1)
    def test_prod_output_rejected(self):
        with self.assertRaises(ValueError):Pipeline(PRODUCTION)
    def test_transcript_available_before_final_diarization(self):
        worker=object.__new__(_Worker);worker.kind='asr';worker.outbox=queue.Queue();worker.process=SimpleNamespace(is_alive=lambda:True);worker.load_seconds=None
        worker.outbox.put({'kind':'ready','load_seconds':.2});worker.outbox.put({'kind':'transcript','id':'job','data':['all words'],'seconds':1.})
        response=worker.receive_transcript('job',time.monotonic()+1);self.assertEqual(response['data'],['all words']);self.assertTrue(worker.outbox.empty())
        worker.outbox.put({'kind':'result','id':'job','data':['all words with speaker metadata'],'seconds':3.})
        self.assertIn('speaker metadata',worker.receive('job',time.monotonic()+1)['data'][0])
if __name__=='__main__':unittest.main()
