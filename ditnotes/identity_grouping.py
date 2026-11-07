"""Conservative regrouping of already-computed project identity embeddings."""
import json
from .features import features


def _regroup_voices(store):
    counts={'face_merges':0,'voice_merges':0,'conflicts_skipped':0}
    if not features()['automatic_voice_grouping']:return counts
    while True:
        names={e['id']:e.get('name') for e in store.people() if not e['merged_into']}
        profiles=[dict(r,vector=json.loads(r['centroid'])) for r in store.db.execute('SELECT * FROM profiles') if r['person_id'] in names]
        proposals=[]
        for a in profiles:
            choices=[]
            for b in profiles:
                if a['person_id']==b['person_id'] or a['model_revision']!=b['model_revision'] or a['dimension']!=b['dimension']:continue
                if names[a['person_id']] and names[b['person_id']] and names[a['person_id']]!=names[b['person_id']]:continue
                choices.append((sum(x*y for x,y in zip(a['vector'],b['vector'])),b['person_id']))
            choices.sort(reverse=True)
            if choices and choices[0][0]>=.82 and (len(choices)==1 or choices[0][0]-choices[1][0]>=.08):proposals.append((choices[0][0],a['person_id'],choices[0][1]))
        changed=False
        for value,a,b in sorted(proposals,reverse=True):
            if names.get(a) and not names.get(b):a,b=b,a
            try:
                store.merge_people(a,b,f'Automatic voice grouping; cosine {value:.4f}; generic threshold 0.82; distinct-identity margin 0.08')
                counts['voice_merges']+=1;changed=True;break
            except ValueError:counts['conflicts_skipped']+=1
        if not changed:return counts


def _regroup_faces(store):
    from itertools import combinations
    from .face_policy import POLICY_ID,face_members,complete_link
    settings=features();threshold=float(settings['face_match_threshold']);floor=float(settings['face_cluster_min_similarity'])
    margin=float(settings['identity_match_margin']);named_threshold=float(settings['face_named_match_threshold'])
    if not all(-1<=v<=1 for v in (threshold,floor,named_threshold)) or not 0<=margin<=2:raise ValueError('Invalid face grouping policy')
    counts={'face_merges':0,'voice_merges':0,'conflicts_skipped':0}
    if not settings['automatic_face_grouping']:return counts
    while True:
        names={e['id']:e.get('name') for e in store.faces() if not e['merged_into']}
        namespaces={}
        for row in store.db.execute('SELECT * FROM face_profiles'):
            if row['face_id'] in names:namespaces.setdefault((row['model_revision'],row['dimension']),[]).append(dict(row,vector=json.loads(row['centroid'])))
        links={r['face_id']:store.canonical_person(r['person_id']) for r in store.db.execute('SELECT * FROM face_voice_links')}
        proposals=[]
        for namespace,profiles in namespaces.items():
            vectors={p['face_id']:p['vector'] for p in profiles};ids=sorted(vectors);members=face_members(store,*namespace)
            scores={tuple(sorted((a,b))):sum(x*y for x,y in zip(vectors[a],vectors[b])) for a,b in combinations(ids,2)}
            support={}
            def score(a,b):return scores[tuple(sorted((a,b)))]
            def compatible(a,b):
                key=tuple(sorted((a,b)))
                if key not in support:
                    support[key]=not (names[a] and names[b] and names[a]!=names[b]) and not store.faces_marked_different(a,b) and not store.face_groups_contradict(a,b) and not (a in links and b in links and links[a]!=links[b]) and complete_link(members.get(a,[]),members.get(b,[]),floor)
                return support[key]
            # Named anchors are distinct identities; fragments of one confirmed
            # name must not create an artificial runner-up competitor.
            for a in ids:
                anchors={}
                for b in ids:
                    if a==b or not names[b] or names[a] and names[a]!=names[b]:continue
                    value=score(a,b);label=names[b]
                    if label not in anchors or value>anchors[label][0]:anchors[label]=(value,b)
                ranked=sorted(anchors.values(),reverse=True)
                if ranked and ranked[0][0]>=named_threshold and (len(ranked)==1 or ranked[0][0]-ranked[1][0]>=margin) and compatible(a,ranked[0][1]):
                    proposals.append((ranked[0][0],a,ranked[0][1],'named_anchor'))
            # Remove anonymous fragment competition only when the entire set of
            # near-tied rivals is mutually supported. Incompatible rivals cause
            # abstention from BOTH directions, rather than a reverse-edge bypass.
            near={a:{a} for a in ids}
            for a in ids:
                if len(ids)<2:continue
                best=max(score(a,b) for b in ids if b!=a)
                near[a].update(b for b in ids if b!=a and score(a,b)>=best-margin)
            for (a,b),value in scores.items():
                if value<threshold or b not in near[a] or a not in near[b]:continue
                component=near[a]|near[b]
                if all(compatible(x,y) for x,y in combinations(component,2)):
                    proposals.append((value,a,b,'supported_component'))
        changed=False
        for value,a,b,basis in sorted(proposals,reverse=True):
            if names.get(a) and not names.get(b):a,b=b,a
            try:
                store.merge_faces(a,b,f'Automatic face grouping; policy {POLICY_ID}; basis {basis}; cosine {value:.4f}; centroid threshold {threshold}; complete-link member floor {floor}; distinct-identity margin {margin}')
                counts['face_merges']+=1;changed=True;break
            except ValueError:counts['conflicts_skipped']+=1
        if not changed:return counts


def regroup(store, *, kinds=('face','voice')):
    """Group selected identity domains; face-only maintenance never edits voices."""
    kinds=tuple(kinds)
    if not kinds or len(set(kinds))!=len(kinds) or any(k not in ('face','voice') for k in kinds):raise ValueError('Choose face and/or voice grouping kinds')
    counts=_regroup_voices(store) if 'voice' in kinds else {'face_merges':0,'voice_merges':0,'conflicts_skipped':0}
    if 'face' in kinds:
        for key,value in _regroup_faces(store).items():counts[key]+=value
    return counts
