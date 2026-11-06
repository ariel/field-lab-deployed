"""MLX diarization + independent speaker-verification embeddings."""
from __future__ import annotations
from collections import defaultdict
import math,os,time
from pathlib import Path
import numpy as np
from .models import ROOT,MODELS,speaker_revision

def normalized_turns(turns,duration):
    rows=[]
    for turn in turns:
        get=turn.get if isinstance(turn,dict) else lambda key,default=None:getattr(turn,key,default)
        a=max(0.,float(get('start')));b=min(float(duration),float(get('end')))
        speaker=get('local_speaker',get('speaker'))
        if not all(math.isfinite(x) for x in (a,b)) or b<=a:continue
        rows.append({'start':a,'end':b,'local_speaker':str(speaker)})
    rows.sort(key=lambda r:(r['start'],r['end'],r['local_speaker']))
    for row in rows:
        row['overlap']=any(other['local_speaker']!=row['local_speaker'] and min(row['end'],other['end'])>max(row['start'],other['start']) for other in rows)
    return rows

def supported_turns(turns,sentences,duration):
    """Public speaker turns require recognized speech support, not music activity.

    Keep the diarizer's raw activity separately. This is transcript diarization;
    it does not assert that every acoustic activity segment contains a person.
    """
    speech=sorted((max(0.,float(x['start'])),min(float(duration),float(x['end']))) for x in sentences if str(x.get('text','')).strip() and float(x['end'])>float(x['start']))
    merged=[]
    for a,b in speech:
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    clipped=[]
    for turn in turns:
        for a,b in merged:
            start,end=max(a,turn['start']),min(b,turn['end'])
            if end>start:clipped.append({'start':start,'end':end,'local_speaker':turn['local_speaker']})
    rows=normalized_turns(clipped,duration)
    for row in rows:row['support']='recognized_speech'
    return rows

def _subtract(interval,others):
    pieces=[interval]
    for a,b in others:
        out=[]
        for start,end in pieces:
            if b<=start or a>=end:out.append((start,end));continue
            if a>start:out.append((start,min(a,end)))
            if b<end:out.append((max(b,start),end))
        pieces=out
    return pieces

def enrollment_windows(turns,sentences,*,min_seconds=2.,max_seconds=6.,max_per_speaker=2):
    """Select bounded clean speech; overlap and ASR-unsupported regions never enroll."""
    if min_seconds<=0 or max_seconds<min_seconds or max_per_speaker<1:raise ValueError('Invalid enrollment window limits')
    speech=[(float(s['start']),float(s['end'])) for s in sentences if str(s.get('text','')).strip() and float(s['end'])>float(s['start'])]
    candidates=defaultdict(list)
    for turn in turns:
        local=turn['local_speaker'];others=[(t['start'],t['end']) for t in turns if t['local_speaker']!=local]
        for a,b in _subtract((turn['start'],turn['end']),others):
            for s,e in speech:
                start,end=max(a,s),min(b,e)
                if end-start<min_seconds:continue
                # One central crop per continuous supported turn, avoiding boundary bleed.
                length=min(max_seconds,end-start);mid=(start+end)/2
                candidates[local].append({'local_speaker':local,'start':mid-length/2,'end':mid+length/2,'supported_seconds':end-start})
    selected=[]
    for local,rows in sorted(candidates.items()):
        kept=[]
        for row in sorted(rows,key=lambda r:(-(r['end']-r['start']),r['start'])):
            if any(min(row['end'],p['end'])>max(row['start'],p['start']) for p in kept):continue
            kept.append(row)
            if len(kept)>=max_per_speaker:break
        selected.extend(kept)
    return sorted(selected,key=lambda r:(r['local_speaker'],r['start']))

def assign_token_speakers(sentences,turns):
    """Attach timing-based candidates without changing transcript wording or tokens."""
    rows=[]
    for sentence_index,sentence in enumerate(sentences):
        tokens=sentence.get('tokens') or [{'start':sentence['start'],'end':sentence['end'],'text':sentence.get('text','')}]
        for token_index,token in enumerate(tokens):
            a=float(token['start']);b=float(token.get('end',a+float(token.get('duration',0))))
            scores=defaultdict(float)
            for turn in turns:
                overlap=max(0.,min(b,turn['end'])-max(a,turn['start']))
                if overlap:scores[turn['local_speaker']]+=overlap
            ranked=sorted(scores,key=lambda speaker:-scores[speaker]);width=max(1e-6,b-a)
            significant=[speaker for speaker in ranked if scores[speaker]/width>=.25]
            chosen=significant[0] if len(significant)==1 and scores[significant[0]]/width>=.5 else None
            rows.append({'sentence_index':sentence_index,'token_index':token_index,'start':a,'end':b,'text':token.get('text',''),
                         'local_speaker':chosen,'speaker_candidates':significant,'overlap':len(significant)>1})
    return rows

def signal_quality(audio,window):
    rms=float(np.sqrt(np.mean(np.asarray(audio,dtype=np.float64)**2))) if len(audio) else 0.
    dbfs=20*math.log10(max(rms,1e-10));clipped=float(np.mean(np.abs(audio)>=.999)) if len(audio) else 1.
    duration=window['end']-window['start'];duration_score=min(1.,duration/3.)
    signal_score=1. if dbfs>=-40 else .3;clipping_score=1. if clipped<=.02 else .3
    components={'duration_seconds':duration,'duration_score':duration_score,'rms_dbfs':dbfs,'clipped_fraction':clipped,'overlap_free':True,'asr_supported':True}
    return min(duration_score,signal_score,clipping_score),components

class DiarizationModels:
    """Reusable local MLX models. Instantiate and call on one serialized GPU worker."""
    def __init__(self,root=ROOT):
        self.root=Path(root);self.diarizer=None;self.speaker=None;self.load_seconds=0.
    def warm(self):
        if self.diarizer is not None:return
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
        for name in ('diarization','speaker'):
            if not (self.root/'models'/name/'model.safetensors').is_file():raise FileNotFoundError('Prepare local models before inference')
        started=time.perf_counter()
        from mlx_audio.vad import load
        from mlx_audio.codec.models.ecapa_tdnn.speaker import EcapaSpeakerEmbeddingExtractor
        self.diarizer=load(self.root/'models/diarization',strict=True)
        self.speaker=EcapaSpeakerEmbeddingExtractor.from_pretrained(self.root/'models/speaker')
        self.load_seconds=time.perf_counter()-started
    def analyze(self,wav,sentences,*,max_windows=2):
        import soundfile as sf
        audio,sr=sf.read(str(wav),dtype='float32')
        if sr!=16000 or audio.ndim!=1:raise ValueError('Diarization requires extracted mono 16kHz audio')
        if not np.isfinite(audio).all():raise ValueError('Audio contains nonfinite samples')
        if not any(str(s.get('text','')).strip() for s in sentences):
            return {'turns':[],'token_speakers':[],'local_speakers':[],'timing':{'diarization_seconds':0.,'identity_seconds':0.},'reason':'No recognized speech to enroll'}
        self.warm();started=time.perf_counter()
        result=self.diarizer.generate(audio,sample_rate=16000,threshold=.5,min_duration=.15,merge_gap=.10,verbose=False)
        raw_turns=normalized_turns(result.segments,len(audio)/sr)
        turns=supported_turns(raw_turns,sentences,len(audio)/sr)
        diarization_seconds=time.perf_counter()-started;started=time.perf_counter()
        windows=enrollment_windows(turns,sentences,max_per_speaker=max_windows)
        encoded=defaultdict(list)
        import mlx.core as mx
        for window in windows:
            crop=audio[round(window['start']*sr):round(window['end']*sr)];quality,components=signal_quality(crop,window)
            if quality<.65:continue
            vector=self.speaker.encode(crop,sample_rate=16000);mx.eval(vector)
            encoded[window['local_speaker']].append({'window':window,'vector':np.array(vector,dtype=np.float32),'quality':quality,'quality_components':components})
        speakers=[]
        for local,rows in sorted(encoded.items()):
            vector=np.average(np.stack([r['vector'] for r in rows]),axis=0,weights=[r['window']['end']-r['window']['start'] for r in rows]);norm=float(np.linalg.norm(vector))
            if not math.isfinite(norm) or norm<=1e-8:continue
            speakers.append({'local_speaker':local,'embedding':(vector/norm).tolist(),'model_revision':speaker_revision(),
                             'quality':min(r['quality'] for r in rows),'quality_components':{'windows':[r['quality_components'] for r in rows],'type':'signal_proxy_not_probability'},
                             'start':min(r['window']['start'] for r in rows),'end':max(r['window']['end'] for r in rows),'enrollment_windows':[r['window'] for r in rows]})
        return {'raw_turns':raw_turns,'turns':turns,'token_speakers':assign_token_speakers(sentences,turns),'local_speakers':speakers,
                'model':MODELS['diarization'],'speaker_model_revision':speaker_revision(),'max_local_speakers':8,
                'timing':{'diarization_seconds':diarization_seconds,'identity_seconds':time.perf_counter()-started,'model_load_seconds':self.load_seconds}}
