import threading,unittest
from lab_indexer.background import BackgroundPipeline

class BackgroundTests(unittest.TestCase):
 def test_warmup_and_jobs_share_one_owner_and_wait_is_reported(self):
  release=threading.Event();calls=[]
  class Fake:
   def __init__(self,*a,**k):self.owner=threading.get_ident()
   def prewarm(self):release.wait(2);calls.append(('warm',threading.get_ident()));return {'discarded':True}
   def analyze(self,source):calls.append(('analyze',threading.get_ident()));return source
   def close(self):calls.append(('close',threading.get_ident()))
  actor=BackgroundPipeline('unused',pipeline_factory=Fake)
  job=actor.analyze('clip');self.assertFalse(job.done());release.set()
  self.assertTrue(actor.warmup.result()['discarded']);result=job.result();actor.close()
  self.assertEqual([x[0] for x in calls],['warm','analyze','close']);self.assertEqual(len({x[1] for x in calls}),1)
  self.assertEqual(result['result'],'clip');self.assertGreaterEqual(result['queue_wait_seconds'],0)
 def test_failed_warmup_prevents_processing(self):
  class Fake:
   def __init__(self,*a,**k):pass
   def prewarm(self):raise ValueError('missing model')
   def analyze(self,*a):raise AssertionError('must not run')
   def close(self):pass
  with BackgroundPipeline('unused',pipeline_factory=Fake) as actor:
   with self.assertRaises(ValueError):actor.analyze('clip').result()
if __name__=='__main__':unittest.main()
