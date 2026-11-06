import http.client,json,sys,tempfile,threading,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from metadata_server import Server
from lab_indexer.project_store import ProjectStore
class EditorTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'projects').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(prefix='api-smoke-',dir=ROOT/'projects');self.project=Path(self.tmp.name)
        (self.project/'catalog.json').write_text(json.dumps({'project':{'name':'Test'},'assets':[{'id':'asset','content_id':'clipsha','name':'clip.mp4','relative_path':'clip.mp4','transcript':[{'start':0,'end':3,'text':'Prairie story'}]}]}))
        with ProjectStore(self.project/'_LAB_NOTES/project.sqlite3') as s:self.person=s.provisional_speaker('clipsha','local0',0,3)['person_id']
        self.server=Server(self.project,0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def req(self,path,values=None,origin=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port);headers={}
        if values is not None:headers['Content-Type']='application/json'
        if origin:headers['Origin']=origin
        c.request('POST' if values is not None else 'GET',path,json.dumps(values).encode() if values is not None else None,headers);r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
    def test_operator_name_and_note_share_projection(self):
        self.assertEqual(self.req('/api/name',{'person_id':self.person,'name':'Ariel'})[0],200)
        status,body=self.req('/api/annotation',{'content_id':'clipsha','text':'Golden hour pickup','metadata':{'tags':['north field']}})
        self.assertEqual(status,200);annotation=json.loads(body)['annotation_id']
        status,body=self.req('/api/project');data=json.loads(body)
        self.assertEqual(data['people'][0]['name'],'Ariel')
        docs=data['projection']['documents'];self.assertEqual(docs[1]['personNames'],['Ariel']);self.assertEqual(docs[-1]['kind'],'operator');self.assertIn('Golden hour',docs[-1]['text'])
        self.assertEqual(self.req('/api/annotation/update',{'annotation_id':annotation,'text':'Blue hour pickup'})[0],200)
        self.assertIn(b'Blue hour',self.req('/api/project')[1])
    def test_local_static_assets_and_boundaries(self):
        for path in ('/','/app.js','/style.css','/orama_projection.mjs','/vendor/orama/index.js'):self.assertEqual(self.req(path)[0],200,path)
        self.assertEqual(self.req('/vendor/orama/../../../../metadata_server.py')[0],404)
        self.assertEqual(self.req('/api/name',{'person_id':self.person,'name':'Other'},origin='https://example.com')[0],403)
        with self.assertRaises(ValueError):Server('/Volumes/ThunderBlade X8/AI Indexer',0)
    def test_face_name_explicit_voice_link_and_crop_boundaries(self):
        with ProjectStore(self.project/'_LAB_NOTES/project.sqlite3') as store:
            face=store.assign_face('clipsha',1,None,'face-fixture',.5,bbox=[.1,.1,.8,.8],crop_ref='/notes/crop.jpg')['face_id']
        notes=self.project/'_DIT_NOTES';notes.mkdir();(notes/'crop.jpg').write_bytes(b'fixture')
        self.assertEqual(self.req('/api/face/name',{'face_id':face,'name':'Portrait'})[0],200)
        data=json.loads(self.req('/api/project')[1]);self.assertIsNone(data['faces'][0]['voice_link']);self.assertEqual(data['faces'][0]['name'],'Portrait')
        self.assertEqual(self.req('/api/face/link',{'face_id':face,'person_id':self.person,'reason':'Operator confirmed'})[0],200)
        self.assertEqual(json.loads(self.req('/api/project')[1])['faces'][0]['voice_link']['person_id'],self.person)
        self.assertEqual(self.req('/notes/crop.jpg')[0],200);self.assertEqual(self.req('/notes/../catalog.json')[0],404)
        self.assertEqual(self.req('/api/face/unlink',{'face_id':face,'reason':'Correction'})[0],200)
    def test_invalid_post_rolls_back(self):
        self.assertEqual(self.req('/api/annotation',{'content_id':'clipsha','text':'x','start':2,'end':1})[0],400)
        self.assertEqual(json.loads(self.req('/api/project')[1])['annotations'],[])
if __name__=='__main__':unittest.main()
