"""Real loopback HTTP tests with release/models -> shared generation symlinks."""
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from ditnotes.server import create_server

class Backend:
    def __init__(self, *args, **kwargs): pass
    def close(self): pass
    def readiness(self): return {'ready': True, 'backend': 'fixture'}

class Metadata:
    def __init__(self, *args, **kwargs): pass
    def close(self): pass

class GenerationAssets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.base = Path(self.temp.name).resolve()
        self.project = self.base / 'project'; self.project.mkdir()
        (self.project / '_DIT_NOTES').mkdir()
        (self.project / '_DIT_NOTES/catalog.json').write_text('{"project":{"id":"fixture"},"assets":[]}')
        self.release = self.base / 'releases/version-one'; self.release.mkdir(parents=True)
        (self.release / 'viewer/dist').mkdir(parents=True)
        (self.release / 'viewer/dist/index.html').write_text('<html>Offline library</html>')
        self.generation = self.base / 'shared/model-generations/first'; self.generation.mkdir(parents=True)
        (self.generation / '.runtime/browser').mkdir(parents=True)
        (self.generation / '.runtime/search-models/embed').mkdir(parents=True)
        self.body = b'\x00asmLOCAL-WASM'
        (self.generation / '.runtime/browser/ort.wasm').write_bytes(self.body)
        (self.generation / '.runtime/search-models/embed/model.bin').write_bytes(b'local-model')
        (self.generation / '.runtime/search-readiness.json').write_text('{"ready":true,"generation":"first"}')
        (self.release / 'models').symlink_to(self.generation)
        with patch('ditnotes.server.SearchBackend', Backend), patch('ditnotes.server.MetadataAPI', Metadata):
            self.server = create_server(self.project, 0, self.release)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.temp.cleanup()
    def request(self, path, method='GET', headers=None):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        c.request(method, path, headers=headers or {}); r = c.getresponse(); result = r.status, dict(r.getheaders()), r.read(); c.close(); return result
    def test_browser_and_models_from_symlinked_generation(self):
        code, headers, body = self.request('/runtime/ort.wasm')
        self.assertEqual(code, 200); self.assertEqual(headers['Content-Type'], 'application/wasm'); self.assertEqual(body, self.body)
        self.assertEqual(self.request('/models/embed/model.bin')[::2], (200, b'local-model'))
        code, headers, body = self.request('/api/readiness'); self.assertEqual(code, 200)
        value = json.loads(body); self.assertTrue(value['ready']); self.assertEqual(value['generation'], 'first'); self.assertTrue(value['backend']['ready'])
    def test_byte_range_and_head(self):
        code, headers, body = self.request('/runtime/ort.wasm', headers={'Range': 'bytes=1-4'})
        self.assertEqual(code, 206); self.assertEqual(body, self.body[1:5]); self.assertEqual(headers['Content-Range'], f'bytes 1-4/{len(self.body)}')
        code, headers, body = self.request('/runtime/ort.wasm', method='HEAD')
        self.assertEqual(code, 200); self.assertEqual(body, b''); self.assertEqual(int(headers['Content-Length']), len(self.body))
    def test_nested_symlink_cannot_expose_external_file(self):
        secret = self.base / 'private.txt'; secret.write_bytes(b'PRIVATE')
        (self.generation / '.runtime/browser/private.wasm').symlink_to(secret)
        self.assertEqual(self.request('/runtime/private.wasm')[0], 403)
        (self.generation / '.runtime/search-readiness.json').unlink()
        (self.generation / '.runtime/search-readiness.json').symlink_to(secret)
        self.assertEqual(self.request('/api/readiness')[0], 403)
    def test_traversal_and_wrong_host_rejected(self):
        self.assertEqual(self.request('/runtime/%2e%2e/search-readiness.json')[0], 403)
        self.assertEqual(self.request('/models/%2e%2e/%2e%2e/private.txt')[0], 403)
        self.assertEqual(self.request('/runtime/ort.wasm', headers={'Host': 'example.com'})[0], 403)
    def test_running_server_remains_anchored_after_model_pointer_switch(self):
        second = self.base / 'shared/model-generations/second'; (second / '.runtime/browser').mkdir(parents=True)
        (second / '.runtime/browser/ort.wasm').write_bytes(b'NEW GENERATION')
        (self.release / 'models').unlink(); (self.release / 'models').symlink_to(second)
        self.assertEqual(self.request('/runtime/ort.wasm')[2], self.body)
        self.assertEqual(json.loads(self.request('/api/readiness')[2])['generation'], 'first')
    def test_ui_and_unknown_routes(self):
        self.assertEqual(self.request('/')[2], b'<html>Offline library</html>')
        self.assertEqual(self.request('/library/review')[0], 200)
        self.assertEqual(self.request('/runtime/missing.wasm')[0], 404)
        self.assertEqual(self.request('/models/embed/missing.bin')[0], 404)

if __name__ == '__main__': unittest.main()
