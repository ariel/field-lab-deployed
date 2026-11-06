"""CPU-only scoring for the small labeled smoke fixture; this is not a DER scorer."""
from __future__ import annotations
import math
import numpy as np

def cosine_matrix(vectors):
    x=np.asarray(vectors,dtype=np.float64)
    if x.ndim!=2 or not np.isfinite(x).all():raise ValueError('Expected finite embedding rows')
    norms=np.linalg.norm(x,axis=1)
    if np.any(norms<1e-9):raise ValueError('Zero embedding')
    x=x/norms[:,None]
    return x@x.T

def pair_summary(rows):
    """Calibrate on enrollment utterances0/1, evaluate heldout2/3 separately."""
    matrix=cosine_matrix([r['embedding'] for r in rows]);same=[];different=[]
    for i,a in enumerate(rows):
        for j,b in enumerate(rows[:i]):
            if a['utterance']>1 or b['utterance']>1:continue
            item={'a':a['id'],'b':b['id'],'cosine':float(matrix[i,j])}
            (same if a['speaker_id']==b['speaker_id'] else different).append(item)
    if not same or not different:raise ValueError('Both same/different calibration pairs required')
    min_same=min(x['cosine'] for x in same);max_different=max(x['cosine'] for x in different)
    separated=min_same>max_different
    threshold=(min_same+max_different)/2 if separated else None
    # Build profiles only from calibration utterances, never held-out probes.
    profiles={}
    for speaker in sorted({r['speaker_id'] for r in rows}):
        values=np.asarray([r['embedding'] for r in rows if r['speaker_id']==speaker and r['utterance']<=1],dtype=np.float64)
        value=values.mean(axis=0);profiles[speaker]=value/np.linalg.norm(value)
    probes=[]
    for row in rows:
        if row['utterance']<=1:continue
        v=np.asarray(row['embedding'],dtype=np.float64);v/=np.linalg.norm(v)
        scores=sorted([{'speaker_id':s,'cosine':float(v@e)} for s,e in profiles.items()],key=lambda x:-x['cosine'])
        probes.append({'id':row['id'],'expected':row['speaker_id'],'ranked':scores,'correct_top1':scores[0]['speaker_id']==row['speaker_id'],
                       'above_calibrated_threshold':None if threshold is None else scores[0]['cosine']>=threshold,'top_two_margin':scores[0]['cosine']-scores[1]['cosine']})
    unknown=[]
    for row in rows:
        if row['speaker_id']!='5639' or row['utterance']<=1:continue
        v=np.asarray(row['embedding'],dtype=np.float64);v/=np.linalg.norm(v)
        score=max(float(v@e) for s,e in profiles.items() if s!='5639')
        unknown.append({'id':row['id'],'max_known_cosine':score,'rejected':None if threshold is None else score<threshold})
    return {'calibration_same_pairs':same,'calibration_different_pairs':different,'minimum_same_cosine':min_same,'maximum_different_cosine':max_different,
            'clean_calibration_separated':separated,'lab_threshold':threshold,'heldout_probes':probes,'heldout_top1_accuracy':sum(r['correct_top1'] for r in probes)/len(probes) if probes else None,
            'heldout_unknown_probes':unknown,'scope':'Three-speaker smoke calibration only; threshold is not approved for production auto identity.'}

def turn_summary(predicted,reference):
    """Utterance-region coverage/assignment, with no claim of strict DER."""
    from scipy.optimize import linear_sum_assignment
    locals=sorted({str(x['local_speaker']) for x in predicted});speakers=sorted({str(x['speaker_id']) for x in reference})
    overlap=np.zeros((len(locals),len(speakers)))
    for p in predicted:
        for r in reference:
            amount=max(0.,min(float(p['end']),float(r['end']))-max(float(p['start']),float(r['start'])))
            overlap[locals.index(str(p['local_speaker'])),speakers.index(str(r['speaker_id']))]+=amount
    rows,cols=linear_sum_assignment(-overlap) if overlap.size else ([],[])
    mapping={locals[i]:speakers[j] for i,j in zip(rows,cols)}
    reference_seconds=sum(float(r['end'])-float(r['start']) for r in reference)
    mapped=sum(float(overlap[i,j]) for i,j in zip(rows,cols))
    return {'local_speakers':locals,'expected_speakers':speakers,'best_overlap_mapping':mapping,'reference_utterance_seconds':reference_seconds,
            'mapped_overlap_seconds':mapped,'mapped_overlap_fraction':mapped/reference_seconds if reference_seconds else None,
            'scope':'Approximate utterance regions include internal silence; not DER. Speaker activity quality needs hand-aligned references.'}
