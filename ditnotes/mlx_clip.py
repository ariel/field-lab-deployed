"""Reusable, local-only OpenAI CLIP embeddings using the official Apple MLX model.

The pinned architecture/preprocessor are vendored from ml-explore/mlx-examples.
Both image and text projections return normalized float32 vectors in the same
512-dimensional space. No PyTorch/ONNX inference is used here.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def _module(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError('Official CLIP module could not be loaded')
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


class ClipModels:
    dimension = 512

    def __init__(self, root: Path = ROOT, batch_size: int = 8):
        self.root = Path(root).resolve()
        self.directory = self.root/'models/mlx-search/clip'
        self.batch_size = max(1, int(batch_size))
        self._lock = threading.RLock()
        self._loaded = False
        self.load_seconds = 0.0
        self.last_image_seconds = 0.0
        self.last_text_seconds = 0.0
        self.revision = None

    def _load(self):
        if self._loaded:
            return
        started = time.perf_counter()
        from prepare_mlx_clip import check
        readiness = check(self.root)
        if not readiness['ready']:
            raise RuntimeError('Local MLX CLIP is not prepared: ' + '; '.join(readiness['errors']))
        import mlx.core as mx
        from tokenizers import Tokenizer
        vendor = self.directory/'_vendor'
        suffix = readiness['implementation_revision'][:12]
        model_module = _module(vendor/'model.py', 'ditnotes._official_clip_model_'+suffix)
        image_module = _module(vendor/'image_processor.py', 'ditnotes._official_clip_processor_'+suffix)
        self.model = model_module.CLIPModel.from_pretrained(str(self.directory))
        self.processor = image_module.CLIPImageProcessor.from_pretrained(str(self.directory))
        self.tokenizer = Tokenizer.from_file(str(self.directory/'tokenizer.json'))
        eos = self.tokenizer.token_to_id('<|endoftext|>')
        if eos is None:
            raise RuntimeError('Prepared CLIP tokenizer is missing its end token')
        self.tokenizer.enable_truncation(max_length=77)
        self.tokenizer.enable_padding(length=77, pad_id=eos, pad_token='<|endoftext|>')
        mx.eval(self.model.parameters())
        self.revision = readiness['revision']['clip']
        self._loaded = True
        self.load_seconds = time.perf_counter()-started

    @staticmethod
    def _normalized(features):
        import mlx.core as mx
        features = features.astype(mx.float32)
        values = features / mx.maximum(mx.linalg.norm(features, axis=-1, keepdims=True), 1e-12)
        mx.eval(values)
        if values.ndim != 2 or values.shape[-1] != 512:
            raise RuntimeError('CLIP returned an unexpected projection size')
        if not bool(mx.all(mx.isfinite(values)).item()):
            raise RuntimeError('CLIP returned nonfinite vectors')
        return values.tolist()

    def embed_images(self, paths):
        from PIL import Image
        import mlx.core as mx
        paths = list(paths)
        if not paths:
            return []
        with self._lock:
            self._load()
            started = time.perf_counter()
            vectors = []
            for offset in range(0, len(paths), self.batch_size):
                images = []
                try:
                    for filename in paths[offset:offset+self.batch_size]:
                        with Image.open(Path(filename)) as image:
                            images.append(image.convert('RGB'))
                    pixels = self.processor(images).astype(mx.float16)
                    vectors.extend(self._normalized(self.model.get_image_features(pixels)))
                finally:
                    for image in images:
                        image.close()
            self.last_image_seconds = time.perf_counter()-started
            return vectors

    def embed_text(self, texts):
        import mlx.core as mx
        texts = [texts] if isinstance(texts, str) else list(texts)
        if not texts:
            return []
        with self._lock:
            self._load()
            started = time.perf_counter()
            encodings = self.tokenizer.encode_batch([str(value) for value in texts], add_special_tokens=True)
            ids = mx.array([encoding.ids for encoding in encodings], dtype=mx.int32)
            vectors = self._normalized(self.model.get_text_features(ids))
            self.last_text_seconds = time.perf_counter()-started
            return vectors
