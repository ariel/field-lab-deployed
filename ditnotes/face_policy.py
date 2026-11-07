"""Versioned conservative grouping of face evidence, independent of embedding IDs."""
import json

POLICY_ID='face-complete-link-v2'
MATCH_THRESHOLD=.65
MEMBER_FLOOR=.50

def face_members(store,revision,dimension):
    """All clean observations support a cluster; enrollment quotas do not hide poses."""
    members={}
    for row in store.db.execute('SELECT face_id,embedding,quality FROM face_observations WHERE model_revision=? AND dimension=?',(revision,dimension)):
        if row['quality']<.7:continue
        vector=json.loads(row['embedding'])
        if vector is not None:members.setdefault(row['face_id'],[]).append(vector)
    return members

def complete_link(left,right,floor):
    # Streaming comparisons bound temporary memory even for a long project.
    return bool(left and right) and all(sum(a*b for a,b in zip(x,y))>=floor for x in left for y in right)
