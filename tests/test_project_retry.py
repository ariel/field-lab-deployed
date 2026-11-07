"""Real project-flock contention is transient; unrelated failures remain failures."""
from pathlib import Path
import tempfile
import threading
import unittest
import contextlib
import io
from unittest.mock import Mock, patch

from ditnotes.library import _lock
from ditnotes.project_retry import retry_project


class ProjectRetry(unittest.TestCase):
    def test_real_project_lock_recovers_after_other_writer_releases(self):
        with tempfile.TemporaryDirectory() as folder:
            notes=Path(folder)/'_DIT_NOTES'
            entered=threading.Event();release=threading.Event()
            def writer():
                with _lock(notes):
                    entered.set();release.wait(3)
            thread=threading.Thread(target=writer);thread.start()
            self.assertTrue(entered.wait(2))
            calls=[]
            def attempt():
                calls.append(1)
                try:
                    with _lock(notes):return 'locked'
                except RuntimeError:
                    release.set()
                    raise
            try:
                self.assertEqual(retry_project(attempt,timeout=2),'locked')
                self.assertGreaterEqual(len(calls),2)
            finally:
                release.set();thread.join(timeout=3)
            self.assertFalse(thread.is_alive())

    def test_continuously_held_real_lock_expires_without_stealing_it(self):
        with tempfile.TemporaryDirectory() as folder:
            notes=Path(folder)/'_DIT_NOTES';calls=[]
            with _lock(notes):
                def attempt():
                    calls.append(1)
                    with _lock(notes):return 'unexpected'
                with self.assertRaisesRegex(RuntimeError,'^Another process is updating this project$'):
                    retry_project(attempt,timeout=.04)
                self.assertGreaterEqual(len(calls),2)
                # The original descriptor is still locked after timeout.
                with self.assertRaises(RuntimeError):
                    with _lock(notes):pass
            with _lock(notes):pass

    def test_nonmatching_failures_pass_through_without_retry_or_sleep(self):
        for error in [RuntimeError('Another process is updating this project: broken state'),RuntimeError('analysis failed'),ValueError('invalid source'),KeyboardInterrupt()]:
            attempt=Mock(side_effect=error)
            with self.subTest(error=repr(error)),patch('ditnotes.project_retry.time.sleep') as sleep:
                with self.assertRaises(type(error)) as caught:retry_project(attempt)
                self.assertIs(caught.exception,error);attempt.assert_called_once();sleep.assert_not_called()

    def test_zero_timeout_attempts_once_and_returns_original_lock_error(self):
        error=RuntimeError('Another process is updating this project');attempt=Mock(side_effect=error)
        with patch('ditnotes.project_retry.time.sleep') as sleep:
            with self.assertRaises(RuntimeError) as caught:retry_project(attempt,timeout=0)
            self.assertIs(caught.exception,error);attempt.assert_called_once();sleep.assert_not_called()

    def test_cli_retries_entry_lock_before_publishing_index(self):
        import dit_notes
        result={'project':'/disposable/project','counts':{'failed':0}}
        process=Mock(side_effect=[RuntimeError('Another process is updating this project'),result])
        backend=Mock()
        with patch('ditnotes.sqlite_safety.require_safe_sqlite'),patch('ditnotes.library.process',process),patch('ditnotes.search_backend.SearchBackend',return_value=backend),patch('ditnotes.enrichment.publish_index',return_value={'ready':True}) as publish,patch('ditnotes.project_retry.time.sleep'),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dit_notes.main(['process','/disposable/project/clip.mp4']),0)
        self.assertEqual(process.call_count,2);publish.assert_called_once();backend.close.assert_called_once()

    def test_cli_publication_collision_retries_without_reprocessing(self):
        import dit_notes
        result={'project':'/disposable/project','counts':{'failed':0}}
        process=Mock(return_value=result);backend=Mock()
        with patch('ditnotes.sqlite_safety.require_safe_sqlite'),patch('ditnotes.library.process',process),patch('ditnotes.search_backend.SearchBackend',return_value=backend),patch('ditnotes.enrichment.publish_index',side_effect=[RuntimeError('Another process is updating this project'),{'ready':True}]) as publish,patch('ditnotes.project_retry.time.sleep'),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dit_notes.main(['process','/disposable/project/clip.mp4']),0)
        process.assert_called_once();self.assertEqual(publish.call_count,2);backend.close.assert_called_once()

    def test_stop_interrupts_lock_wait_without_waiting_for_deadline(self):
        stop=threading.Event();entered=threading.Event();outcome=[]
        def attempt():entered.set();raise RuntimeError('Another process is updating this project')
        def run():
            try:retry_project(attempt,timeout=60,stop_event=stop)
            except KeyboardInterrupt:outcome.append('stopped')
        thread=threading.Thread(target=run);thread.start();self.assertTrue(entered.wait(1))
        stop.set();thread.join(1)
        self.assertFalse(thread.is_alive());self.assertEqual(outcome,['stopped'])

    def test_invalid_deadlines_never_invoke_operation(self):
        for timeout in [-1,float('nan'),float('inf')]:
            attempt=Mock()
            with self.subTest(timeout=timeout),self.assertRaises(ValueError):retry_project(attempt,timeout)
            attempt.assert_not_called()

if __name__=='__main__':unittest.main()
