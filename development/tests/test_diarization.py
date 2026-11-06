import unittest
from lab_indexer.diarization import normalized_turns,enrollment_windows,assign_token_speakers,supported_turns
class DiarizationTests(unittest.TestCase):
    def test_enrollment_excludes_overlap_and_bounds_work(self):
        turns=normalized_turns([{'start':0,'end':20,'speaker':0},{'start':5,'end':8,'speaker':1}],20)
        windows=enrollment_windows(turns,[{'start':0,'end':20,'text':'complete speech'}],max_per_speaker=2)
        self.assertTrue(windows)
        for w in windows:
            self.assertLessEqual(w['end']-w['start'],6)
            self.assertTrue(w['end']<=5 or w['start']>=8)
        self.assertLessEqual(len(windows),2)
    def test_no_asr_support_never_enrolls(self):
        turns=normalized_turns([{'start':0,'end':20,'speaker':0}],20)
        self.assertEqual(enrollment_windows(turns,[]),[])
    def test_overlap_kept_ambiguous_and_transcript_unchanged(self):
        sentences=[{'start':1,'end':3,'text':'Hello','tokens':[{'start':1,'end':2,'text':'Hello'}]}]
        rows=assign_token_speakers(sentences,normalized_turns([{'start':0,'end':3,'speaker':0},{'start':1,'end':2,'speaker':1}],3))
        self.assertIsNone(rows[0]['local_speaker']);self.assertTrue(rows[0]['overlap']);self.assertEqual(rows[0]['text'],'Hello')
        self.assertEqual(sentences[0]['text'],'Hello')
    def test_music_activity_never_becomes_a_speaker_turn(self):
        raw=normalized_turns([{'start':0,'end':20,'speaker':'music'},{'start':25,'end':30,'speaker':'voice'}],40)
        turns=supported_turns(raw,[{'start':25,'end':30,'text':'A narrator speaks'}],40)
        self.assertEqual({t['local_speaker'] for t in turns},{'voice'})
        self.assertEqual(len(raw),2)
    def test_token_matching(self):
        rows=assign_token_speakers([{'start':1,'end':2,'text':'a'}],normalized_turns([{'start':0,'end':3,'speaker':0}],3))
        self.assertEqual(rows[0]['local_speaker'],'0')
if __name__=='__main__':unittest.main()
