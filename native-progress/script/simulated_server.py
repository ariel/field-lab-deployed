"""CPU-only protocol fixture; never reads/writes production."""
from http.server import BaseHTTPRequestHandler,HTTPServer
import json,time
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  value={'protocol_version':1,'stage':'asr_vlm','current':'20261101/A001/Test clip.mp4','total':5,'completed':2,'failed':0,'started_at':time.time()-93,'updated_at':time.time(),'elapsed':93}
  body=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
HTTPServer(('127.0.0.1',18767),Handler).serve_forever()
