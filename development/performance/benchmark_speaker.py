#!/usr/bin/env python3
"""Run only after the parent reserves a GPU window. Local pinned assets only."""
from __future__ import annotations
import argparse,json,os,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'performance'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--gpu-authorized',action='store_true');args=p.parse_args()
 if not args.gpu_authorized:p.error('Parent GPU-window authorization is required before running this benchmark')
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
 from lab_indexer.models import check,speaker_revision
 ready=check(ROOT)
 if not ready['ready']:raise RuntimeError(ready)
 import soundfile as sf
 import numpy as np
 from evaluate_speakers import pair_summary
 started=time.perf_counter()
 import mlx.core as mx
 from mlx_audio.codec.models.ecapa_tdnn.speaker import EcapaSpeakerEmbeddingExtractor
 model=EcapaSpeakerEmbeddingExtractor.from_pretrained(ROOT/'models/speaker')
 load_seconds=time.perf_counter()-started
 manifest=json.loads((ROOT/'fixtures/manifest.json').read_text());rows=[]
 for item in manifest['samples']:
  audio,sr=sf.read(ROOT/'fixtures'/item['path'],dtype='float32');assert sr==16000 and audio.ndim==1
  length=min(len(audio),6*sr);offset=(len(audio)-length)//2;crop=audio[offset:offset+length]
  start=time.perf_counter();v=model.encode(crop,sample_rate=sr);mx.eval(v);embedding=np.asarray(v,dtype=np.float32).tolist();elapsed=time.perf_counter()-start
  rows.append({**item,'crop_start':offset/sr,'crop_seconds':length/sr,'wall_seconds':elapsed,'embedding':embedding})
  print(json.dumps({'id':item['id'],'seconds':elapsed}),flush=True)
 report={'model_revision':speaker_revision(),'device':str(mx.default_device()),'model_load_seconds':load_seconds,'embedding_rows':rows,'scores':pair_summary(rows),
         'scope':'Independent speaker embedding calibration, not full pipeline throughput or universal speaker quality. Every waveform is local; no audio sent to a service.'}
 path=ROOT/'benchmarks/speaker-embedding.json';path.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'load_seconds':load_seconds,'min_same':report['scores']['minimum_same_cosine'],'max_different':report['scores']['maximum_different_cosine'],'heldout_top1':report['scores']['heldout_top1_accuracy'],'lab_threshold':report['scores']['lab_threshold'],'path':str(path)}))
if __name__=='__main__':main()
