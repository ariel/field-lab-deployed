"""Local-only role/routing regressions. No model downloads or inference."""
import io,json,errno,tempfile,threading,unittest,subprocess
import urllib.error
from ditnotes import chat as chat_module
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock,AsyncMock
from contextlib import nullcontext
from ditnotes import library
from ditnotes.engine import Engine
from ditnotes.chat import make_agent,ChatService
from ditnotes.model_roles import FAST_VISION_MODEL,CHAT_MODEL,model_path

class ModelRoles(unittest.TestCase):
 def test_ingest_keeps_fast_model_without_creating_workers(self):
  with tempfile.TemporaryDirectory() as folder:
   engine=Engine(models_root=folder)
   try:
    self.assertEqual(engine.paths['vlm'],Path(folder).resolve()/FAST_VISION_MODEL)
    self.assertEqual(engine.workers,{})
    self.assertNotEqual(engine.paths['vlm'].name,CHAT_MODEL)
   finally:engine.close()
 def test_model_paths_distinguish_both_roles(self):
  root=Path('/application')
  self.assertEqual(model_path(root,'ingest_vision'),root/'models/Qwen3.5-4B-4bit')
  self.assertEqual(model_path(root,'agentic_chat'),root/'models/Qwen3.8-27B-4bit')
  with self.assertRaises(ValueError):model_path(root,'unregistered')
 def test_chat_only_weights_and_role_metadata_do_not_reindex_ingest(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'deploy').mkdir()
   lock={'model_files':[{'path':'Qwen3.5-4B-4bit/model.safetensors','sha256':'a'*64,'bytes':20}], 'model_json':{}}
   def save():(root/'deploy/assets.lock.json').write_text(json.dumps(lock))
   save()
   with patch.object(library,'ROOT',root):
    original=library.profile_id()
    lock['model_files'].append({'path':CHAT_MODEL+'/model-00001-of-00004.safetensors','sha256':'b'*64,'bytes':40})
    lock['model_roles']={'agentic_chat':CHAT_MODEL};save()
    self.assertEqual(library.profile_id(),original)
    lock['model_files'][-1]['sha256']='c'*64;lock['model_roles']['revision']='updated-chat';save()
    self.assertEqual(library.profile_id(),original)
    lock['model_files'][0]['sha256']='d'*64;save()
    self.assertNotEqual(library.profile_id(),original)



class ServerIdentity(unittest.TestCase):
 def test_big_checkpoint_must_be_actually_loaded(self):
  expected='/release/models/'+CHAT_MODEL
  self.assertTrue(chat_module.server_has_model({'data':[{'id':expected,'loaded':True}]},expected))
  for row in [
   {'id':expected,'loaded':False},
   {'id':expected},
   {'id':'/release/models/'+FAST_VISION_MODEL,'loaded':True},
   {'id':'/previous/models/'+CHAT_MODEL,'loaded':True},
   {'id':CHAT_MODEL,'loaded':True},
  ]:
   with self.subTest(row=row):self.assertFalse(chat_module.server_has_model({'data':[row]},expected))
 def test_loaded_small_model_does_not_make_cached_big_model_ready(self):
  expected='/release/models/'+CHAT_MODEL
  models={'data':[{'id':'/release/models/'+FAST_VISION_MODEL,'loaded':True},{'id':expected,'loaded':False}]}
  self.assertFalse(chat_module.server_has_model(models,expected))
 def test_chat_port_can_be_isolated_without_external_host_configuration(self):
  with patch.dict('os.environ',{'FIELD_LAB_CHAT_PORT':'18788'}):
   self.assertEqual(chat_module.chat_base_url(),'http://127.0.0.1:18788/v1')
  for value in ['0','65536','remote.example','8768/other']:
   with self.subTest(value=value),patch.dict('os.environ',{'FIELD_LAB_CHAT_PORT':value}):
    with self.assertRaises(ValueError):chat_module.chat_port()
 def test_existing_wrong_or_unloaded_server_is_not_replaced(self):
  for models in [{'data':[{'id':'/release/models/'+FAST_VISION_MODEL,'loaded':True}]},{'data':[]}]:
   with self.subTest(models=models),tempfile.TemporaryDirectory() as folder:
    service=ChatService.__new__(ChatService);service.server=SimpleNamespace(tool_root=Path(folder));service.model_process=None
    with patch.object(chat_module,'read_server_models',return_value=models),patch.object(chat_module.subprocess,'Popen') as spawn:
     with self.assertRaises(RuntimeError):service.ensure_model()
     spawn.assert_not_called();self.assertIsNone(service.model_process)
 def test_existing_exact_loaded_big_server_is_reused_without_claiming_ownership(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);service=ChatService.__new__(ChatService);service.server=SimpleNamespace(tool_root=root);service.model_process=None
   models={'data':[{'id':chat_module.chat_model_id(root),'loaded':True}]}
   with patch.object(chat_module,'read_server_models',return_value=models),patch.object(chat_module.subprocess,'Popen') as spawn:
    service.ensure_model();spawn.assert_not_called();self.assertIsNone(service.model_process)


class ServerProbeFailures(unittest.TestCase):
 def response(self,data):
  response=io.BytesIO(data);response.status=200;return response
 def test_probe_reads_json_without_environment_proxy(self):
  response=self.response(b'{"data":[]}');opener=Mock();opener.open.return_value=response
  with patch.object(chat_module.urllib.request,'build_opener',return_value=opener) as build:
   self.assertEqual(chat_module.read_server_models('http://127.0.0.1:18788/v1'),{'data':[]})
   self.assertEqual(build.call_args.args[0].proxies,{})
  opener.open.assert_called_once_with('http://127.0.0.1:18788/v1/models',timeout=1)
 def test_only_refusal_means_port_is_free(self):
  errors=[urllib.error.URLError(ConnectionRefusedError(errno.ECONNREFUSED,'refused')),urllib.error.URLError(TimeoutError('busy')),urllib.error.HTTPError('http://127.0.0.1/models',404,'other app',None,None),ConnectionResetError('reset')]
  for i,error in enumerate(errors):
   opener=Mock();opener.open.side_effect=error
   with self.subTest(error=type(error).__name__),patch.object(chat_module.urllib.request,'build_opener',return_value=opener):
    if i==0:self.assertIsNone(chat_module.read_server_models('http://127.0.0.1:18788/v1'))
    else:
     with self.assertRaises(RuntimeError):chat_module.read_server_models('http://127.0.0.1:18788/v1')
 def test_invalid_json_is_not_a_free_port(self):
  opener=Mock();opener.open.return_value=self.response(b'not a model inventory')
  with patch.object(chat_module.urllib.request,'build_opener',return_value=opener):
   with self.assertRaises(RuntimeError):chat_module.read_server_models('http://127.0.0.1:18788/v1')
 def test_wrong_model_responding_during_start_cannot_be_accepted(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder).resolve();service=ChatService.__new__(ChatService);service.server=SimpleNamespace(tool_root=root);service.model_process=None
   child=Mock();child.poll.return_value=None
   wrong={'data':[{'id':str(root/'models'/FAST_VISION_MODEL),'loaded':True}]}
   with patch.object(chat_module,'read_server_models',side_effect=[None,wrong]),patch('dit_notes.model_readiness',return_value={CHAT_MODEL:{'ready':True}}),patch.object(chat_module.subprocess,'Popen',return_value=child) as spawn:
    with self.assertRaisesRegex(RuntimeError,'different or unverified'):service.ensure_model()
   args=spawn.call_args.args[0];self.assertEqual(args[args.index('--model')+1],chat_module.chat_model_id(root));child.terminate.assert_called_once()
 def test_missing_big_weights_never_starts_the_small_model(self):
  with tempfile.TemporaryDirectory() as folder:
   service=ChatService.__new__(ChatService);service.server=SimpleNamespace(tool_root=Path(folder));service.model_process=None
   with patch.object(chat_module,'read_server_models',return_value=None),patch('dit_notes.model_readiness',return_value={CHAT_MODEL:{'ready':False}}),patch.object(chat_module.subprocess,'Popen') as spawn:
    with self.assertRaisesRegex(RuntimeError,'not prepared'):service.ensure_model()
    spawn.assert_not_called()
 def test_shutdown_prevents_starting_a_model(self):
  service=ChatService.__new__(ChatService);service.server=SimpleNamespace(tool_root=Path('/application'));service.model_process=None;service.closing=threading.Event();service.closing.set()
  with patch.object(chat_module,'read_server_models') as probe,patch.object(chat_module.subprocess,'Popen') as spawn:
   with self.assertRaisesRegex(RuntimeError,'shutting down'):service.ensure_model()
   probe.assert_not_called();spawn.assert_not_called()

class ChatShutdown(unittest.TestCase):
 def test_close_drains_chat_writer_before_returning(self):
  events=[];service=ChatService.__new__(ChatService)
  service.executor=Mock();service.executor.shutdown.side_effect=lambda **kw:events.append(('shutdown',kw))
  process=Mock();process.poll.return_value=None;service.model_process=process
  process.terminate.side_effect=lambda:events.append(('terminate',None))
  service.close()
  service.executor.shutdown.assert_called_once_with(wait=True,cancel_futures=True)
  process.terminate.assert_called_once()
  self.assertIsNone(service.model_process)
  self.assertLess(next(i for i,x in enumerate(events) if x[0]=='terminate'),next(i for i,x in enumerate(events) if x[0]=='shutdown'))
 def test_close_does_not_terminate_an_unowned_server(self):
  service=ChatService.__new__(ChatService);service.model_process=None;service.executor=Mock()
  service.close();service.executor.shutdown.assert_called_once_with(wait=True,cancel_futures=True)

class OwnedModelCleanup(unittest.TestCase):
 def test_graceful_owned_shutdown_is_reaped_and_idempotent(self):
  service=ChatService.__new__(ChatService);service.lock=threading.Lock()
  process=Mock();process.poll.return_value=None;service.model_process=process
  service.stop_owned_model();service.stop_owned_model()
  process.terminate.assert_called_once();process.wait.assert_called_once_with(timeout=5)
  process.kill.assert_not_called();self.assertIsNone(service.model_process)
 def test_unresponsive_owned_server_is_killed_and_reaped(self):
  service=ChatService.__new__(ChatService);service.lock=threading.Lock()
  process=Mock();process.poll.return_value=None;process.wait.side_effect=[subprocess.TimeoutExpired('mlx',5),0];service.model_process=process
  service.stop_owned_model()
  process.terminate.assert_called_once();process.kill.assert_called_once()
  self.assertEqual(process.wait.call_count,2);self.assertIsNone(service.model_process)
 def test_already_exited_owned_process_is_reaped_without_signals(self):
  service=ChatService.__new__(ChatService);process=Mock();process.poll.return_value=1;service.model_process=process
  service.stop_owned_model()
  process.wait.assert_called_once_with(timeout=5);process.terminate.assert_not_called();process.kill.assert_not_called()
 def test_completed_turn_unloads_model_and_closes_tools(self):
  service=ChatService.__new__(ChatService);service.update=Mock();service.ensure_model=Mock();service.stop_owned_model=Mock();service.server=Mock()
  database=Mock();database.execute.return_value=[];service.store=lambda:nullcontext(SimpleNamespace(db=database))
  tools=Mock();tools.documents=[];tools.shown=[]
  answer=SimpleNamespace(outcome='explanation',answer='Done')
  with patch.object(chat_module,'FootageTools',return_value=tools),patch.object(chat_module,'run_agent',new=AsyncMock(return_value=(answer,'[]'))):
   service.run('turn','session','question')
  service.stop_owned_model.assert_called_once();tools.close.assert_called_once()
  self.assertEqual(service.update.call_args.kwargs['status'],'complete')
 def test_failed_turn_unloads_owned_model_and_records_error(self):
  service=ChatService.__new__(ChatService);service.update=Mock();service.ensure_model=Mock(side_effect=RuntimeError('test startup failure'));service.stop_owned_model=Mock()
  service.run('turn','session','question')
  service.stop_owned_model.assert_called_once()
  self.assertEqual(service.update.call_args.kwargs['status'],'error')
  self.assertEqual(service.update.call_args.kwargs['results'],'[]')

class AgentModelRole(unittest.IsolatedAsyncioTestCase):
 async def test_agent_uses_big_model_without_network_request(self):
  agent,client=make_agent()
  try:
   self.assertEqual(Path(agent.model.model_name).name,CHAT_MODEL)
   self.assertNotEqual(Path(agent.model.model_name).name,FAST_VISION_MODEL)
  finally:await client.aclose()

if __name__=='__main__':unittest.main()
