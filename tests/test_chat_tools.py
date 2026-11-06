import unittest
from types import SimpleNamespace
from ditnotes.chat_tools import FootageTools

class Tools(unittest.TestCase):
 def test_together_is_an_identity_constraint_not_a_clip_embedding_query(self):
  t=FootageTools.__new__(FootageTools);t.notify=lambda *a:None;t.pool={};calls=[]
  t.person=lambda name:{'faces':[{'id':name.lower(),'name':name}]}
  row={'id':'both','assetId':'clip','contentId':'content','path':'clip.mp4','title':'clip.mp4','seconds':12,'kind':'visual','text':'Two people','faceIds':['vince','howard']}
  def call(**kw):calls.append(kw);return {'rows':[row]}
  t.call=call;t.frames=lambda ids:SimpleNamespace(content=[])
  result=t.search_shots(['Vince','Howard'],'together in the same frame')
  self.assertEqual(calls,[{'action':'identity','filters':{'faceGroups':[['vince'],['howard']]}}])
  self.assertEqual(result.return_value['candidate_count'],1);self.assertEqual(t.combined_search['scene'],'')
 def test_person_lookup_filters_face_ids_without_embedding_the_name(self):
  t=FootageTools.__new__(FootageTools);t.notify=lambda *a:None;t.pool={};calls=[]
  t.person=lambda name:{'faces':[{'id':'face_vince','name':name}],'voices':[]}
  row={'id':'shot','assetId':'clip','contentId':'content','path':'clip.mp4','title':'clip.mp4','seconds':12,'kind':'visual','text':'Red suspenders','faceIds':['face_vince'],'faceNames':['Vince']}
  def call(**kw):calls.append(kw);return {'rows':[row]}
  t.call=call
  t.frames=lambda ids:SimpleNamespace(return_value={'frames':[]},content=[])
  def present(ids):raise AssertionError('Research must not publish candidates')
  t.present=present
  r=t.search_person('Vince')
  self.assertEqual(calls,[{'action':'identity','filters':{'faceId':'face_vince'}}])
  self.assertEqual(r.return_value['matching_sampled_frames'],1);self.assertIn('shot',t.pool)
  self.assertTrue(r.return_value['candidate_only']);self.assertNotIn('opened_shots',r.return_value)
 def test_failed_final_answer_discards_staged_person_examples(self):
  from ditnotes.chat_answer import ChatAnswer
  t=FootageTools.__new__(FootageTools);t.shown=[{'id':'naboo-only'}]
  t.commit_answer(ChatAnswer(outcome='not_verified',answer="I couldn't verify a matching shot.",result_ids=[]))
  self.assertEqual(t.shown,[])
 def test_partial_person_match_cannot_be_published_as_conjunction(self):
  from ditnotes.chat_answer import ChatAnswer,VisualEvidence
  t=FootageTools.__new__(FootageTools);t.required_face_groups=[['vince'],['naboo']];t.combined_search={'scene':'shop'};t.inspected={'shot'}
  t.pool={'shot':{'kind':'visual','faceIds':['naboo','bollo']}}
  a=ChatAnswer(outcome='matched',answer='A match',result_ids=['shot'],visual_evidence=[VisualEvidence(result_id='shot',visible_support='Interior')])
  with self.assertRaisesRegex(ValueError,'all requested'):t.validate_answer(a)
 def test_named_face_provenance_is_distinct_from_caption_and_voice(self):
  t=FootageTools.__new__(FootageTools)
  t.identity_state={'faces':[{'id':'face_1','name':'Vince','voice_link':None}]}
  row={'id':'shot','assetId':'clip','title':'Clip.mp4','kind':'visual','seconds':194,'text':'Person in red suspenders','source':'ai_visual','faceIds':['face_1'],'faceNames':[],'personNames':[],'identityBasis':'visual_face'}
  r=t.compact(row)
  self.assertEqual(r['visible_names'],['Vince'])
  self.assertEqual(r['text_source'],'ai_visual')
  self.assertEqual(r['face_identity_evidence'][0]['name_source'],'operator_face_group_label')
  self.assertIsNone(r['face_identity_evidence'][0]['voice_link'])
 def test_explanation_joins_current_label_to_the_exact_visual_observation(self):
  t=FootageTools.__new__(FootageTools);t.notify=lambda *a:None
  t.pool={'shot':{'id':'shot','assetId':'clip','title':'Clip.mp4','kind':'visual','seconds':194,'text':'Red suspenders','faceIds':['face_1'],'faceNames':['Old label']}}
  t.assets={'clip':{'content_id':'content'}}
  state={'faces':[{'id':'face_1','name':'Vince'}],'face_observations':[{'content_id':'content','face_id':'face_1','seconds':194,'bbox':[.1,.1,.3,.4]},{'content_id':'content','face_id':'other','seconds':20}]}
  t.server=SimpleNamespace(metadata=SimpleNamespace(state=lambda:state))
  r=t.explain_identity('shot')
  self.assertEqual(r['visible_names'],['Vince'])
  self.assertEqual(len(r['face_observations']),1)
  self.assertEqual(r['face_observations'][0]['bbox'],[.1,.1,.3,.4])
 def test_face_identity_uses_face_filter_in_shared_index(self):
  t=FootageTools.__new__(FootageTools);t.notify=lambda *_:None;t.pool={};calls=[]
  t.infer=lambda *a:{'vectors':[[1]]}
  def call(**kw):calls.append(kw);return {'rows':[]}
  t.call=call
  t.search('Ariel',person_id='face_123')
  self.assertEqual(calls[0]['filters'],{'faceId':'face_123'})
  t.search('Ariel',person_id='person_123')
  self.assertEqual(calls[1]['filters'],{'personId':'person_123'})
 def test_duplicate_evidence_becomes_one_grounded_shot(self):
  t=FootageTools.__new__(FootageTools);t.notify=lambda *_:None;t.pool={}
  for key,kind,time in [('spoken','speech',14.48),('visual','visual',14.014)]:
   t.pool[key]={'id':key,'kind':kind,'seconds':time,'contentId':'sha','assetId':'clip','title':'Trailer.mp4','text':'Bison','image':'/notes/frame.jpg'}
  result=t.present(['spoken','visual']);self.assertEqual(len(t.shown),1);self.assertEqual(t.shown[0]['seconds'],14.014);self.assertEqual({r['id'] for r in t.shown[0]['evidence']},{'spoken','visual'});self.assertIn('#shot=visual',result['shots'][0]['citation_url'])
 def test_transcript_poster_cannot_masquerade_as_a_timed_visual_frame(self):
  t=FootageTools.__new__(FootageTools);t.pool={'speech':{'kind':'speech','image':'/notes/poster.jpg'}}
  with self.assertRaisesRegex(ValueError,'thumbnails are not timed frames'):t.frames(['speech'])
 def test_unknown_retrieval_id_cannot_open_a_file(self):
  t=FootageTools.__new__(FootageTools);t.pool={}
  with self.assertRaisesRegex(ValueError,'retrieved'):t.present(['../../private'])

if __name__=='__main__':unittest.main()
