#!/usr/bin/env python3
"""Download a small, attributed LibriSpeech test subset and make CPU-only fixtures."""
from __future__ import annotations
import hashlib,json,urllib.request
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'fixtures';AUDIO=OUT/'librispeech';AUDIO.mkdir(parents=True,exist_ok=True)
DATASET='openslr/librispeech_asr';CONFIG='clean';SPLIT='test'
REVISION='71cacbfb7e2354c4226d01e70d77d5fca3d04ba1'
SPEAKERS=(6930,1320,5639)
def fetch_json(url):return json.load(urllib.request.urlopen(url,timeout=30))
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rows=[]
for offset in (0,100):
 result=fetch_json(f'https://datasets-server.huggingface.co/rows?dataset={DATASET}&config={CONFIG}&split={SPLIT}&offset={offset}&length=100')
 rows.extend(result['rows'])
manifest={'dataset':DATASET,'revision':REVISION,'config':CONFIG,'split':SPLIT,'license':'CC-BY-4.0','attribution':'LibriSpeech ASR corpus, Panayotov et al.; OpenSLR SLR12; recordings from LibriVox public-domain audiobooks. Dataset source https://www.openslr.org/12 and https://huggingface.co/datasets/openslr/librispeech_asr','scope':'Three labeled dataset speaker IDs; utterance boundaries are approximate speech regions, not a hand-aligned diarization reference. This is a smoke fixture, not field-quality certification.','samples':[],'composites':[]}
arrays={}
for speaker in SPEAKERS:
 chosen=[r for r in rows if r['row']['speaker_id']==speaker][:4]
 for i,item in enumerate(chosen):
  row=item['row'];url=row['audio'][0]['src'];assert '/--/'+REVISION+'/--/' in url
  path=AUDIO/f'speaker-{speaker}-{i}.flac'
  if not path.exists():
   with urllib.request.urlopen(url,timeout=30) as response:path.write_bytes(response.read())
  audio,rate=sf.read(path,dtype='float32');assert rate==16000 and audio.ndim==1
  arrays[(speaker,i)]=audio
  manifest['samples'].append({'speaker_id':str(speaker),'utterance':i,'id':row['id'],'row_index':item['row_idx'],'text':row['text'],'path':str(path.relative_to(OUT)),'sha256':sha(path),'seconds':len(audio)/rate,'sample_rate':rate})
def composite(name,order):
 parts=[];segments=[];cursor=0;silence=np.zeros(5600,dtype=np.float32)
 for speaker,i in order:
  a=arrays[(speaker,i)];start=cursor/16000;parts.append(a);cursor+=len(a)
  segments.append({'start':start,'end':cursor/16000,'speaker_id':str(speaker),'source':f'librispeech/speaker-{speaker}-{i}.flac'})
  parts.append(silence);cursor+=len(silence)
 path=OUT/name;sf.write(path,np.concatenate(parts),16000,subtype='PCM_16')
 entry={'path':name,'seconds':cursor/16000,'sha256':sha(path),'sample_rate':16000,'segments':segments,'reference_kind':'source-utterance extents; internal silence and pronunciation pauses are not annotated; do not report strict DER'}
 manifest['composites'].append(entry)
 return entry
composite('cross-clip-a.wav',[(6930,0),(1320,0),(5639,0),(6930,1),(1320,1),(5639,1)])
composite('cross-clip-b.wav',[(5639,2),(6930,2),(1320,2),(5639,3),(1320,3),(6930,3)])
# An unseen third speaker can be held out of enrollment while testing open-set rejection.
manifest['open_set_protocol']={'enroll_speakers':['6930','1320'],'unknown_speaker':'5639','held_out_probes':'utterances 2 and 3; enrollment uses 0 and 1','warning':'Do not tune and report accuracy on the same probe pairs.'}
# Nonspeech controls and a labeled overlap construction.
sf.write(OUT/'silence.wav',np.zeros(16000*6,dtype=np.float32),16000,subtype='PCM_16')
rng=np.random.default_rng(427);noise=rng.normal(0,.03,16000*6).astype(np.float32);sf.write(OUT/'noise.wav',noise,16000,subtype='PCM_16')
a=arrays[(6930,2)][:16000*6];b=arrays[(1320,2)][:16000*6]
overlap=np.zeros(max(len(a),len(b)+32000),dtype=np.float32);overlap[:len(a)]+=.45*a;overlap[32000:32000+len(b)]+=.45*b
sf.write(OUT/'overlap.wav',overlap,16000,subtype='PCM_16')
manifest['controls']=[{'path':'silence.wav','expected':'no speaker identity'},{'path':'noise.wav','expected':'no speaker identity'},{'path':'overlap.wav','speaker_sources':['6930','1320'],'source_regions':[{'start':0,'end':len(a)/16000,'speaker_id':'6930'},{'start':2,'end':2+len(b)/16000,'speaker_id':'1320'}],'expected':'overlap is not clean enrollment; no forced new person from mixed voice'}]
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'samples':len(manifest['samples']),'composite_seconds':[x['seconds'] for x in manifest['composites']],'speaker_ids':list(SPEAKERS)},indent=2))
