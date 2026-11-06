"""Shutdown/locking tests use only temp files and fake daemon/UI/model objects."""
import contextlib
import fcntl
import http.client
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import ingest_service as service

class Clock:
    def __init__(self):self.now=0;self.on_sleep=lambda _:None
    def monotonic(self):return self.now
    def sleep(self,seconds):self.now+=seconds;self.on_sleep(seconds)

class Shutdown(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'runtime').mkdir()
        self.pid=987654321
        (self.root/'runtime/service.json').write_text(json.dumps({'pid':self.pid}))
    def hold_lock(self):
        lock=(self.root/'runtime/service.lock').open('a+')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);self.addCleanup(lock.close);return lock
    @contextlib.contextmanager
    def fake_stop_environment(self,clock,kill):
        with patch.object(service,'ROOT',self.root),patch.object(service.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout=str(self.root)+'/ingest_service.py run\n')),patch.object(service.os,'killpg',side_effect=kill),patch.object(service.time,'monotonic',clock.monotonic),patch.object(service.time,'sleep',clock.sleep):yield
    def test_sigkill_path_waits_until_lock_released(self):
        held=self.hold_lock();clock=Clock();signals=[];post_kill_sleeps=[]
        def kill(pid,sig):self.assertEqual(pid,self.pid);signals.append(sig)
        def sleep(_):
            if signal.SIGKILL in signals:
                post_kill_sleeps.append(clock.now)
                if len(post_kill_sleeps)==3:held.close()
        clock.on_sleep=sleep
        with self.fake_stop_environment(clock,kill):result=service.stop_service()
        self.assertEqual(signals,[signal.SIGTERM,signal.SIGKILL]);self.assertEqual(len(post_kill_sleeps),3)
        self.assertEqual(result['status'],'stopped');self.assertIn('resume',result['incomplete_work'])
    def test_sigkill_timeout_never_reports_stopped_with_lock_held(self):
        self.hold_lock();clock=Clock();signals=[]
        with self.fake_stop_environment(clock,lambda _,sig:signals.append(sig)):
            with self.assertRaisesRegex(RuntimeError,'still owns its lock'):service.stop_service()
        self.assertEqual(signals,[signal.SIGTERM,signal.SIGKILL]);self.assertGreaterEqual(clock.now,13)
    def test_graceful_stop_waits_for_lock_without_sigkill(self):
        held=self.hold_lock();clock=Clock();signals=[];sleeps=[]
        def sleep(_):
            sleeps.append(clock.now)
            if len(sleeps)==3:held.close()
        clock.on_sleep=sleep
        with self.fake_stop_environment(clock,lambda _,sig:signals.append(sig)):result=service.stop_service()
        self.assertEqual(signals,[signal.SIGTERM]);self.assertEqual(result,{'status':'stopped'});self.assertEqual(len(sleeps),3)
    def test_missing_pid_with_live_lock_is_unknown(self):
        self.hold_lock();(self.root/'runtime/service.json').unlink()
        with patch.object(service,'ROOT',self.root):
            with self.assertRaisesRegex(RuntimeError,'unknown, not stopped'):service.stop_service()
    def test_unrelated_pid_with_live_lock_is_unknown(self):
        self.hold_lock()
        with patch.object(service,'ROOT',self.root),patch.object(service.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout='unrelated-program')),patch.object(service.os,'killpg') as kill:
            with self.assertRaisesRegex(RuntimeError,'unknown, not stopped'):service.stop_service()
            kill.assert_not_called()
    def test_missing_pid_with_no_lock_owner_is_stopped(self):
        (self.root/'runtime/service.json').unlink()
        with patch.object(service,'ROOT',self.root):self.assertEqual(service.stop_service(),{'status':'stopped'})
    def test_run_holds_service_lock_until_writer_thread_finishes(self):
        project=self.root/'project';project.mkdir();config={'ingest_root':str(project),'port':0,'queue_db':str(self.root/'runtime/queue.sqlite3')}
        worker_started=threading.Event();release_worker=threading.Event();server_closed=threading.Event();finished=threading.Event();errors=[];queries=[]
        class DB:
            def execute(self,query):queries.append(query);return self
            def fetchone(self):return ('ok',)
        class Server:
            def serve_forever(self,**kwargs):
                if not worker_started.wait(3):raise AssertionError('worker did not start')
            def shutdown(self):pass
            def server_close(self):server_closed.set()
        class Controller:
            def __init__(self,*args):pass
            def status(self):return {}
            def loop(inner):
                worker_started.set()
                if not release_worker.wait(10):raise AssertionError('test failed to release writer')
                (self.root/'runtime/final-writer-checkpoint').write_text('all writer work finished')
                finished.set()
        def run():
            try:service.run()
            except BaseException as error:errors.append(error)
        with patch.object(service,'ROOT',self.root),patch.object(service,'config',return_value=config),patch.object(service,'verify_volume'),patch.object(service,'connect',side_effect=lambda _:contextlib.nullcontext(DB())),patch.object(service,'Controller',Controller),patch.object(service,'Snapshots',return_value=SimpleNamespace(vectors=lambda:{})),patch('ditnotes.server.create_server',return_value=Server()),patch.object(service.signal,'signal'):
            runner=threading.Thread(target=run,daemon=True);runner.start()
            try:
                self.assertTrue(worker_started.wait(3));runner.join(timeout=2.2)
                self.assertTrue(runner.is_alive(),'run returned while its writer was still active')
                self.assertFalse(server_closed.is_set(),'server resources closed before ingest writer finished')
                self.assertFalse((self.root/'runtime/stopped.json').exists());self.assertFalse(finished.is_set())
                self.assertNotIn('PRAGMA wal_checkpoint(TRUNCATE)',queries)
                with (self.root/'runtime/service.lock').open('a+') as probe:
                    with self.assertRaises(BlockingIOError):fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:
                release_worker.set();runner.join(timeout=3)
            self.assertFalse(runner.is_alive());self.assertEqual(errors,[]);self.assertTrue(finished.is_set())
            self.assertTrue(server_closed.is_set())
            self.assertTrue((self.root/'runtime/stopped.json').exists());self.assertIn('PRAGMA wal_checkpoint(TRUNCATE)',queries)
            with (self.root/'runtime/service.lock').open('a+') as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)

    def test_metadata_close_waits_for_publisher_to_finish(self):
        from ditnotes.metadata_api import MetadataAPI
        publisher_started=threading.Event();release_publisher=threading.Event();publisher_done=threading.Event()
        def publish():
            publisher_started.set();release_publisher.wait(10)
            (self.root/'publisher-checkpoint').write_text('committed');publisher_done.set()
        api=MetadataAPI.__new__(MetadataAPI);api.stop=threading.Event();api.changed=threading.Event()
        api.thread=threading.Thread(target=publish,daemon=True);api.thread.start();self.assertTrue(publisher_started.wait(2))
        closer=threading.Thread(target=api.close,daemon=True);closer.start()
        try:
            closer.join(timeout=2.2);self.assertTrue(closer.is_alive());self.assertFalse(publisher_done.is_set())
            self.assertTrue(api.stop.is_set());self.assertTrue(api.changed.is_set())
        finally:release_publisher.set();closer.join(timeout=3)
        self.assertFalse(closer.is_alive());self.assertTrue(publisher_done.is_set())

    def test_server_drains_mutating_handler_before_closing_resources(self):
        from ditnotes import server as http_server
        project=self.root/'project';(project/'_DIT_NOTES').mkdir(parents=True)
        (project/'_DIT_NOTES/catalog.json').write_text('{"project":{"id":"test"},"assets":[]}')
        tool=self.root/'tool';tool.mkdir();started=threading.Event();release=threading.Event();events=[];errors=[]
        class Backend:
            def __init__(self,*args,**kwargs):pass
            def close(self):events.append('backend-closed')
        class Metadata:
            def __init__(self,*args,**kwargs):pass
            def close(self):events.append('metadata-closed')
        def handler(h):
            started.set();release.wait(10)
            (project/'operator-save-fixture').write_text('committed')
            events.append('handler-committed');h.send_response(200);h.send_header('Content-Length','0');h.end_headers()
        with patch.object(http_server,'SearchBackend',Backend),patch.object(http_server,'MetadataAPI',Metadata),patch.object(http_server._Handler,'do_POST',handler):
            server=http_server.create_server(project,0,tool)
            listener=threading.Thread(target=server.serve_forever,daemon=True);listener.start()
            def request():
                try:
                    conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10);conn.request('POST','/fixture');response=conn.getresponse();response.read();conn.close()
                except BaseException as e:errors.append(e)
            client=threading.Thread(target=request,daemon=True);client.start();self.assertTrue(started.wait(3))
            server.shutdown();listener.join(timeout=2)
            closer=threading.Thread(target=server.server_close,daemon=True);closer.start()
            try:
                closer.join(timeout=.2);self.assertTrue(closer.is_alive());self.assertEqual(events,[])
            finally:release.set();client.join(timeout=3);closer.join(timeout=3)
            self.assertFalse(closer.is_alive());self.assertFalse(client.is_alive());self.assertEqual(errors,[])
            self.assertEqual(events,['handler-committed','metadata-closed','backend-closed'])

if __name__=='__main__':unittest.main()
