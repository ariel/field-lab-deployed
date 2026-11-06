"""Local MiniLM embedding and cross-encoder inference through maintained mlx-vlm models.

No custom model architecture, model conversion or core-package changes. Instantiate/use
on one dedicated serialized thread. Both inference paths use MLX on Apple Silicon.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import time


class TextModels:
    dimensions=384
    def __init__(self,localroot=None,*,batch_size=32):
        root=Path(localroot or Path(__file__).resolve().parents[1]).resolve()
        # Accept the tool root or the exact models/mlx-search directory.
        self.root=root if (root/'text/config.json').is_file() else root/'models/mlx-search'
        self.batch_size=int(batch_size)
        if self.batch_size<1:raise ValueError('batch_size must be positive')
        for kind in ('text','reranker'):
            for filename in ('config.json','tokenizer.json','model.safetensors'):
                if not (self.root/kind/filename).is_file():raise FileNotFoundError('Local MLX text assets missing; run prepare_mlx_text.prepare(tool_root)')
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
        started=time.perf_counter()
        import mlx.core as mx
        from mlx_vlm.embedding_loader import load_embedding_model
        from mlx_vlm.reranker_loader import load_sequence_classification_model
        from transformers import AutoTokenizer
        self.mx=mx
        self.text=load_embedding_model(self.root/'text',strict=True)
        self.text.pooling_config=json.loads((self.root/'text/1_Pooling/config.json').read_text())
        self.reranker=load_sequence_classification_model(self.root/'reranker',strict=True)
        self.text_tokenizer=AutoTokenizer.from_pretrained(str(self.root/'text'),local_files_only=True,trust_remote_code=False)
        self.rerank_tokenizer=AutoTokenizer.from_pretrained(str(self.root/'reranker'),local_files_only=True,trust_remote_code=False)
        self.load_seconds=time.perf_counter()-started
        self.last_timing={}
    def _inputs(self,encoded):
        return {key:self.mx.array(value) for key,value in encoded.items() if key in ('input_ids','attention_mask','token_type_ids')}
    def embed(self,texts):
        texts=list(texts)
        if not all(isinstance(text,str) for text in texts):raise TypeError('Embedding inputs must be strings')
        started=time.perf_counter();vectors=[]
        for offset in range(0,len(texts),self.batch_size):
            batch=texts[offset:offset+self.batch_size]
            encoded=self.text_tokenizer(batch,padding=True,truncation=True,max_length=256,return_tensors='np')
            result=self.text(**self._inputs(encoded)).text_embeds
            self.mx.eval(result);vectors.extend(result.tolist())
        self.last_timing['embed_seconds']=time.perf_counter()-started
        return vectors
    def rerank(self,query,documents):
        documents=list(documents)
        if not isinstance(query,str) or not all(isinstance(doc,str) for doc in documents):raise TypeError('Reranker inputs must be strings')
        started=time.perf_counter();scores=[]
        for offset in range(0,len(documents),self.batch_size):
            batch=documents[offset:offset+self.batch_size]
            encoded=self.rerank_tokenizer([query]*len(batch),batch,padding=True,truncation='longest_first',max_length=512,return_tensors='np')
            logits=self.reranker(**self._inputs(encoded)).logits[:,0]
            self.mx.eval(logits);scores.extend(logits.tolist())
        self.last_timing['rerank_seconds']=time.perf_counter()-started
        return scores
