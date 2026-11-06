#!/usr/bin/env python3
"""Isolated diarization/identity timing with reference transcripts; not ASR timing."""
from __future__ import annotations
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'performance'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--gpu-authorized',action='store_true');p.add_argument('--only',default=None);args=p.parse_args()
 if not args.gpu_authorized:p.error('Parent GPU-window authorization is required')
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
 from lab_indexer.diarization import DiarizationModels
 from evaluate_speakers import turn_summary
 manifest=json.loads((ROOT/'fixtures/manifest.json').read_text());texts={r['path']:r['text'] for r in manifest['samples']}
 started=time.perf_counter();models=DiarizationModels(ROOT);models.warm();load=time.perf_counter()-started;results=[]
 for item in manifest['composites']:
  if args.only and item['path']!=args.only:continue
  sentences=[{'start':s['start'],'end':s['end'],'text':texts[s['source']]} for s in item['segments']]
  started=time.perf_counter();output=models.analyze(ROOT/'fixtures'/item['path'],sentences);wall=time.perf_counter()-started
  row={'source':item,'wall_seconds':wall,'ratio':wall/item['seconds'],'load_seconds':load,'diarization':output,'turn_quality':turn_summary(output['turns'],item['segments'])}
  results.append(row);print(json.dumps({'path':item['path'],'wall':wall,'ratio':row['ratio'],'local_speaker_count':len(output['local_speakers']),'stage_timing':output['timing'],'turn_quality':row['turn_quality']}),flush=True)
 report={'scope':'MLX diarization and voice embedding stage only, reference transcript extents supplied; not complete postprocessing throughput and not strict DER','runs':results}
 (ROOT/'benchmarks/diarization.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
