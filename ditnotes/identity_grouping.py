"""Conservative regrouping of already-computed project identity embeddings."""
import json
from .features import features

def regroup(store):
    counts={'face_merges':0,'voice_merges':0,'conflicts_skipped':0}
    for kind,table,key,entities,threshold in [('face','face_profiles','face_id',store.faces,.8),('voice','profiles','person_id',store.people,.82)]:
        if not features()['automatic_'+kind+'_grouping']:continue
        while True:
            names={e['id']:e.get('name') for e in entities() if not e['merged_into']}
            profiles=[dict(r,vector=json.loads(r['centroid'])) for r in store.db.execute('SELECT * FROM '+table) if r[key] in names]
            proposals=[]
            for a in profiles:
                if kind=='face':
                    # Anonymous fragments of the SAME named person are not
                    # rival identities. Compare distinct operator names, then
                    # retain a margin over the next differently named person.
                    anchors={}
                    for b in profiles:
                        if a[key]==b[key] or not names.get(b[key]) or a['model_revision']!=b['model_revision'] or a['dimension']!=b['dimension']:continue
                        if names.get(a[key]) and names[a[key]]!=names[b[key]]:continue
                        if store.faces_marked_different(a[key],b[key]):continue
                        score=sum(x*y for x,y in zip(a['vector'],b['vector']))
                        label=names[b[key]]
                        if label not in anchors or score>anchors[label][0]:anchors[label]=(score,b[key])
                    ranked=sorted(anchors.values(),reverse=True)
                    if ranked and ranked[0][0]>=features()['face_named_match_threshold'] and (len(ranked)==1 or ranked[0][0]-ranked[1][0]>=features()['identity_match_margin']):
                        proposals.append((ranked[0][0],a[key],ranked[0][1]));continue
                choices=[]
                for b in profiles:
                    if a[key]==b[key] or a['model_revision']!=b['model_revision'] or a['dimension']!=b['dimension']:continue
                    if names[a[key]] and names[b[key]] and names[a[key]]!=names[b[key]]:continue
                    if kind=='face' and store.faces_marked_different(a[key],b[key]):continue
                    choices.append((sum(x*y for x,y in zip(a['vector'],b['vector'])),b[key]))
                choices.sort(reverse=True)
                if choices and choices[0][0]>=threshold and (len(choices)==1 or choices[0][0]-choices[1][0]>=.08):
                    proposals.append((choices[0][0],a[key],choices[0][1]))
            changed=False
            for score,a,b in sorted(proposals,reverse=True):
                # Retain named IDs where possible, so existing names/links survive.
                if names.get(a) and not names.get(b):a,b=b,a
                try:
                    reason=f'Automatic {kind} grouping; cosine {score:.4f}; named-face threshold {features()["face_named_match_threshold"]} / generic threshold {threshold}; distinct-identity margin 0.08'
                    if kind=='face':store.merge_faces(a,b,reason)
                    else:store.merge_people(a,b,reason)
                    counts[kind+'_merges']+=1;changed=True;break
                except ValueError:counts['conflicts_skipped']+=1
            if not changed:break
    return counts
