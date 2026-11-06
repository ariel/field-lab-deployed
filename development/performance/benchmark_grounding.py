#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
 p=argparse.ArgumentParser();p.add_argument('--gpu-authorized',action='store_true');a=p.parse_args()
 if not a.gpu_authorized:p.error('Parent GPU window required')
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
 import mlx.core as mx
 from mlx_vlm import load,generate
 from mlx_vlm.prompt_utils import apply_chat_template
 from lab_indexer.audio_context import contextual_prompt
 started=time.perf_counter();model,processor=load('/Volumes/ThunderBlade X8/AI Indexer/models/Qwen3.5-4B-4bit');model.set_dtype(mx.float16);load_seconds=time.perf_counter()-started
 base=(ROOT/'lab_indexer/prompts/field-caption.txt').read_text();rows=[]
 for case in json.loads((ROOT/'fixtures/visual-context-cases.json').read_text()):
  prompt=contextual_prompt(base,case['seconds'],case['audio_context']);formatted=apply_chat_template(processor,model.config,prompt,num_images=1,enable_thinking=False)
  started=time.perf_counter();r=generate(model,processor,formatted,image=[str(ROOT/'fixtures'/case['image'])],max_tokens=36,temperature=0.,verbose=False);wall=time.perf_counter()-started;text=r.text.strip()
  forbidden=[term for term in case['forbidden_visual_terms'] if re.search(r'\b'+re.escape(term)+r'\b',text,re.I)]
  row={**case,'caption':text,'wall_seconds':wall,'forbidden_terms_present':forbidden,'expected_visual_term_present':any(re.search(r'\b'+re.escape(t)+r'\b',text,re.I) for t in case['expected_visual_terms_any'])};rows.append(row);print(json.dumps({'id':case['id'],'caption':text,'seconds':wall,'forbidden':forbidden}),flush=True)
 (ROOT/'benchmarks/vlm-grounding.json').write_text(json.dumps({'load_seconds':load_seconds,'cases':rows,'scope':'Two targeted prompt-grounding smoke cases; not a general visual accuracy benchmark.'},indent=2))
if __name__=='__main__':main()
