"""Same-machine MLX inference; Orama in the browser still owns retrieval/indexing."""
from concurrent.futures import ThreadPoolExecutor
import json
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

class SearchBackend:
    def __init__(self, root, image_resolver, *, warm_start=False):
        self.root=Path(root);self.image_resolver=image_resolver
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='local-mlx-search')
        self.text=None;self.clip=None;self.warmup_future=None;self.warmup_seconds=None;self.warmup_error=None
        if warm_start:self.warm()
    def readiness(self):
        try:
            a=json.loads((self.root/'models/.runtime/mlx-text-readiness.json').read_text())
            b=json.loads((self.root/'models/.runtime/mlx-clip-readiness.json').read_text())
            revisions={**a.get('revision',{}),**b.get('revision',{})}
            return {'type':'mlx','ready':bool(not self.warmup_error and a.get('ready') and b.get('ready') and all(revisions.get(k) for k in ('text','clip','reranker'))),'revision':revisions,'warming':bool(self.warmup_future and not self.warmup_future.done()),'warmup_seconds':self.warmup_seconds,'error':self.warmup_error}
        except (OSError,ValueError):return {'type':'mlx','ready':False,'revision':{}}
    def warm(self):
        """Start local model loading/compilation without blocking process startup."""
        if self.warmup_future is None and self.readiness()['ready']:
            self.warmup_future=self.executor.submit(self._warm_models)
        return self.warmup_future
    def _warm_models(self):
        started=time.perf_counter()
        try:
            self._infer('embed_text',['Camera footage and recorded dialogue.']*8,'')
            self._infer('rerank',['Camera footage.','Recorded dialogue.'],'footage')
            self._infer('embed_clip_text',['camera footage'],'')
            from PIL import Image
            with tempfile.TemporaryDirectory(prefix='ditnotes-warmup-') as directory:
                path=Path(directory)/'frame.jpg'
                Image.new('RGB',(224,224),(128,128,128)).save(path)
                self._infer('embed_images',[path],'')
        except Exception as error:
            self.warmup_error=str(error)
            raise
        finally:self.warmup_seconds=time.perf_counter()-started
    def call(self, payload):
        if not self.readiness()['ready']:raise ValueError('Local MLX search models are not prepared')
        if not isinstance(payload,dict):raise ValueError('Expected a JSON object')
        action=payload.get('action')
        if action not in ('embed_text','embed_clip_text','embed_images','rerank'):raise ValueError('Unknown model operation')
        key='urls' if action=='embed_images' else 'texts';values=payload.get(key)
        if not isinstance(values,list) or not 1<=len(values)<=40 or any(not isinstance(x,str) or len(x)>20000 for x in values):raise ValueError('Expected 1–40 bounded strings')
        if action=='embed_images':values=[self.image_resolver(x) for x in values]
        query=payload.get('query','')
        if not isinstance(query,str) or len(query)>10000:raise ValueError('Invalid query')
        return self.executor.submit(self._infer,action,values,query).result(timeout=120)
    def _infer(self,action,values,query):
        if action in ('embed_text','rerank'):
            if self.text is None:
                from .mlx_text import TextModels
                self.text=TextModels(self.root)
            if action=='rerank':return {'scores':self.text.rerank(query,values)}
            return {'vectors':self.text.embed(values)}
        if self.clip is None:
            from .mlx_clip import ClipModels
            self.clip=ClipModels(self.root)
        return {'vectors':self.clip.embed_images(values) if action=='embed_images' else self.clip.embed_text(values)}
    def close(self):self.executor.shutdown(wait=True,cancel_futures=True)

def serve_model_request(handler, backend):
    """POST model inference only; require same-origin JSON and bounded body."""
    host=handler.headers.get('Host','')
    if host not in (f'127.0.0.1:{handler.server.server_port}',f'localhost:{handler.server.server_port}'):
        handler.send_error(403);return
    origin=handler.headers.get('Origin')
    if origin and origin not in (f'http://127.0.0.1:{handler.server.server_port}',f'http://localhost:{handler.server.server_port}'):
        handler.send_error(403);return
    if urlsplit(handler.path).path!='/api/search-models':handler.send_error(404);return
    if handler.headers.get('Content-Type','').split(';')[0]!='application/json':handler.send_error(415);return
    try:
        length=int(handler.headers.get('Content-Length','0'))
        if not 0<length<=1024*1024:raise ValueError('Invalid request size')
        result=backend.call(json.loads(handler.rfile.read(length)));code=200
    except Exception as e:result={'error':str(e)};code=503
    body=json.dumps(result,allow_nan=False).encode();handler.send_response(code);handler.send_header('Content-Type','application/json');handler.send_header('Content-Length',str(len(body)));handler.send_header('Cache-Control','no-store');handler.end_headers();handler.wfile.write(body)
