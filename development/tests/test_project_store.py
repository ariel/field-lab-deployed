import json,math,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lab_indexer.project_store import ProjectStore
from lab_indexer.search_projection import project_documents
class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'project.sqlite';self.s=ProjectStore(self.path,'test-project')
    def tearDown(self):self.s.close();self.temp.cleanup()
    def voice(self,clip,label,start,vector,**kwargs):
        return self.s.assign_speaker(clip,label,start,start+3,vector,'ecapa192:rev:frontend-v1',.9,**kwargs)
    def test_open_set_identity_and_repeat(self):
        a=self.voice('a','spk0',0,[1,0,0],auto_assign=True)
        b=self.voice('b','spk0',0,[.99,.01,0],auto_assign=True)
        c=self.voice('c','spk0',0,[0,1,0],auto_assign=True)
        self.assertEqual(a['person_id'],b['person_id']);self.assertNotEqual(a['person_id'],c['person_id'])
        rev=self.s.edit_revision;self.assertEqual(self.voice('b','spk0',0,[.99,.01,0])['person_id'],b['person_id']);self.assertEqual(rev,self.s.edit_revision)
    def test_uncalibrated_matching_is_provisional(self):
        a=self.voice('a','spk0',0,[1,0]);b=self.voice('b','spk0',0,[1,0])
        self.assertNotEqual(a['person_id'],b['person_id']);self.assertEqual(b['status'],'provisional');self.assertEqual(b['candidates'][0]['person_id'],a['person_id'])
    def test_low_quality_overlap_and_namespace(self):
        a=self.voice('a','spk0',0,[1,0],auto_assign=True)
        b=self.s.assign_speaker('b','spk0',0,3,[1,0],'ecapa192:rev:frontend-v1',.2,quality_components={'overlap':False},auto_assign=True)
        self.assertEqual(b['status'],'insufficient_evidence')
        c=self.voice('a','spk1',1,[1,0],auto_assign=True)
        self.assertNotEqual(c['person_id'],a['person_id'])
        d=self.s.assign_speaker('d','spk0',0,3,[1,0],'different-model-revision',.9,auto_assign=True)
        self.assertNotEqual(d['person_id'],a['person_id'])
        with self.assertRaises(ValueError):self.s.assign_speaker('e','spk0',0,3,[1,0,0],'ecapa192:rev:frontend-v1',.9,auto_assign=True)
        self.assertEqual(len(self.s.db.execute('SELECT * FROM profiles WHERE person_id=?',(b['person_id'],)).fetchall()),0)
    def test_names_merge_split_and_restart(self):
        a=self.voice('a','spk0',0,[1,0]);b=self.voice('b','spk0',0,[0,1])
        self.s.name_person(a['person_id'],'Ariel');self.s.name_person(b['person_id'],'Matt')
        with self.assertRaises(ValueError):self.s.merge_people(b['person_id'],a['person_id'],'review')
        self.s.merge_people(b['person_id'],a['person_id'],'operator confirmed same voice',chosen_name='Ariel')
        self.assertEqual(self.s.observations('b')[0]['person_id'],a['person_id'])
        new=self.s.split_person(a['person_id'],[b['observation_id']],'operator corrected mistaken merge',new_name='Matt')
        self.assertEqual(self.s.observations('b')[0]['person_id'],new)
        revision=self.s.edit_revision;self.s.close();self.s=ProjectStore(self.path,'test-project')
        self.assertEqual(self.s.edit_revision,revision);self.assertEqual(self.s.observations('a')[0]['person_id'],a['person_id'])
        self.assertTrue(any(e['operation']=='person_split' for e in self.s.audit()))
    def test_annotations_and_link_provenance(self):
        note=self.s.add_annotation('a','Prairie burn pickup',metadata={'location':'north field'})
        self.s.add_annotation('b','Different human note')
        links=self.s.suggest_links('b',[1,0],{'a':{'vector':[.99,.01],'model_revision':'clip:rev:mean12'}},'clip:rev:mean12',threshold=.95)
        self.assertEqual(len(links),1);self.assertEqual(len(self.s.annotations('b')),1)
        rev=self.s.edit_revision;self.s.suggest_links('b',[1,0],{'a':{'vector':[.99,.01],'model_revision':'clip:rev:mean12'}},'clip:rev:mean12',threshold=.95);self.assertEqual(rev,self.s.edit_revision)
        self.s.update_annotation(note,'Later edited source note')
        self.assertEqual(self.s.links('b')[0]['annotation_snapshot']['text'],'Prairie burn pickup')
        accepted=self.s.accept_link(links[0]['id']);self.assertEqual(accepted,self.s.accept_link(links[0]['id']))
        result=self.s.annotations('b');self.assertEqual(len(result),2);self.assertEqual(result[1]['source'],'accepted_inheritance');self.assertEqual(result[1]['text'],'Prairie burn pickup');self.assertEqual(result[1]['metadata']['source_annotation_id'],note)
        self.assertIsNone(result[1]['start']);self.assertIsNone(result[1]['end'])
        self.assertEqual(self.s.annotations('a')[0]['text'],'Later edited source note')
        with self.assertRaises(ValueError):self.s.suggest_links('b',[1,0],{'a':{'vector':[1,0],'model_revision':'wrong'}},'clip:rev:mean12')
    def test_projection_preserves_existing_ids_and_adds_metadata(self):
        voice=self.voice('sha','s0',1,[1,0]);self.s.name_person(voice['person_id'],'Ariel')
        note=self.s.add_annotation('sha','Magic hour pickup',start=1,end=2,metadata={'take':3})
        catalog={'assets':[{'id':'asset','content_id':'sha','name':'clip.mp4','relative_path':'Day/clip.mp4','highlights':[{'seconds':1.5,'note':'A field'}],'transcript':[{'start':1,'end':3,'text':'A prairie story.'}]}]}
        projection=project_documents(catalog,self.s);docs=projection['documents']
        self.assertEqual([d['id'] for d in docs[:3]],['asset:file','asset:visual:0','asset:speech:0:0'])
        self.assertEqual(docs[2]['personNames'],['Ariel']);self.assertEqual(docs[3]['kind'],'operator');self.assertIn(note,docs[3]['id']);self.assertIn('Magic hour',docs[3]['text'])
    def test_transaction_rolls_back(self):
        a=self.voice('a','s0',0,[1,0]);before=len(self.s.people());rev=self.s.edit_revision
        with self.assertRaises(ValueError):self.s.split_person(a['person_id'],[a['observation_id']],'')
        self.assertEqual(len(self.s.people()),before);self.assertEqual(self.s.edit_revision,rev)
    def test_provisional_turn_never_invents_embedding(self):
        a=self.s.provisional_speaker('a','s0',0,.5,reason='short_speech')
        self.assertIsNone(a['embedding']);self.assertEqual(a['dimension'],0)
        self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM profiles').fetchone()[0],0)
        b=self.voice('a','s0',1,[1,0])
        self.assertEqual(a['person_id'],b['person_id']);self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM profiles').fetchone()[0],1)
    def test_overlap_exclusions_are_stream_local(self):
        a=self.voice('a','mic0:s0',0,[1,0],auto_assign=True,overlap_group='mic0')
        b=self.voice('a','mic1:s0',0,[1,0],auto_assign=True,overlap_group='mic1')
        c=self.voice('a','mic0:s1',1,[1,0],auto_assign=True,overlap_group='mic0')
        self.assertEqual(a['person_id'],b['person_id'])
        self.assertNotEqual(a['person_id'],c['person_id'])
    def test_enrollment_cap(self):
        for i in range(8):self.voice('a','s0',i*4,[1,0])
        self.assertEqual(self.s.db.execute('SELECT SUM(enrolled) FROM observations').fetchone()[0],3)
if __name__=='__main__':unittest.main()
