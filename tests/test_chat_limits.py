import unittest
from types import SimpleNamespace
from unittest.mock import patch,AsyncMock
from pydantic_ai.messages import ModelResponse,TextPart,ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.exceptions import UsageLimitExceeded
from ditnotes.chat import make_agent,run_agent
from ditnotes.chat import text_history

class Limits(unittest.IsolatedAsyncioTestCase):
 def test_prior_images_are_not_reused_as_current_visual_evidence(self):
  from pydantic_ai.messages import ModelRequest,UserPromptPart,BinaryContent
  original=[ModelRequest(parts=[UserPromptPart(['Previous evidence',BinaryContent(data=b'image',media_type='image/jpeg')])])]
  result=text_history(original)
  self.assertIsInstance(original[0].parts[0].content[1],BinaryContent)
  self.assertIsInstance(result[0].parts[0].content[1],str)
 async def test_repeated_investigation_gets_a_final_answer_turn(self):
  calls=[]
  def model(messages,info):
   names=[t.name for t in info.function_tools];calls.append(names)
   if 'search_footage' in names:
    return ModelResponse(parts=[ToolCallPart('search_footage',{'query':'bison'})])
   if 'show_results' in names:
    return ModelResponse(parts=[ToolCallPart('show_results',{'result_ids':['candidate']})])
   return ModelResponse(parts=[ToolCallPart('answer',{'outcome':'not_verified','answer':'I could not verify a same-shot match. These are separate appearances.','result_ids':[]})])
  agent,client=make_agent()
  tools=SimpleNamespace(search=lambda *a:[],present=lambda *a:{'shots':[]},shown=[],notify=lambda *a:None)
  with agent.override(model=FunctionModel(model)),patch('ditnotes.chat.make_agent',return_value=(agent,client)):
   answer,history=await run_agent('Find both in the same shot',tools,[])
  self.assertIn('could not verify',answer.answer)
  self.assertEqual(len(calls),9)
  self.assertEqual(calls[-2],['show_results']);self.assertEqual(calls[-1],[])
  self.assertIn('separate appearances',history)

 async def test_hard_guard_discards_candidates_without_leaking_framework_error(self):
  agent=SimpleNamespace(run=AsyncMock(side_effect=UsageLimitExceeded('request_limit of 10')))
  client=SimpleNamespace(aclose=AsyncMock());events=[]
  tools=SimpleNamespace(shown=[{'id':'candidate'}],notify=lambda *a:events.append(a))
  with patch('ditnotes.chat.make_agent',return_value=(agent,client)):
   answer,history=await run_agent('Find both in the same shot',tools,[])
  self.assertIn('before completing verification',answer.answer)
  self.assertNotIn('candidate shots below',answer.answer)
  self.assertNotIn('request_limit',answer.answer)
  self.assertIn('Find both in the same shot',history);self.assertIn('before completing verification',history)
  self.assertEqual(len(tools.shown),0);client.aclose.assert_awaited_once()

if __name__=='__main__':unittest.main()
