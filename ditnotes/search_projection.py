"""One projection for AI evidence, people facets and durable operator metadata.

These records go to the existing Orama text/hybrid index. Image records retain
CLIP512 vectors; speaker enrollment embeddings are never document embeddings.
"""
from __future__ import annotations
from copy import deepcopy
import json


def _chunks(text,size=85):
    words=text.strip().split()
    return [' '.join(words[i:i+size]) for i in range(0,len(words),size)]

def _metadata_text(value):
    if isinstance(value,dict):return ' '.join(str(k)+': '+_metadata_text(v) for k,v in sorted(value.items()))
    if isinstance(value,list):return ' '.join(_metadata_text(v) for v in value)
    if value is None:return ''
    return str(value)

def project_documents(catalog,store):
    names={p['id']:p['name'] for p in store.people() if not p['merged_into']}
    face_entities={f['id']:f for f in store.faces() if not f['merged_into']}
    docs=[]
    for asset in catalog.get('assets',[]):
        asset_id=str(asset['id']);content=asset.get('content_id') or asset_id
        observations=store.observations(content)
        faces=store.face_observations(content)
        def face_fields(selected):
            ids=sorted({f['face_id'] for f in selected});linked=sorted({face_entities[f]['voice_link']['person_id'] for f in ids if face_entities.get(f,{}).get('voice_link')})
            return {'faceIds':ids,'faceNames':[face_entities[f]['name'] for f in ids if face_entities.get(f,{}).get('name')], 'linkedPersonIds':linked}
        def visible(base,selected):
            fields=face_fields(selected);linked=fields.pop('linkedPersonIds');base.update(fields)
            base['personIds']=sorted(set(base['personIds']+linked));base['personNames']=[names[p] for p in base['personIds'] if names.get(p)]
            base['identityBasis']='operator_linked_face' if linked else 'visual_face'
            return base
        def base(start=0,end=None,all_people=False,voice_presence=True):
            if not voice_presence:selected=[]
            elif all_people:selected=observations
            elif end is None:selected=[o for o in observations if o['start']<=start<o['end']]
            else:selected=[o for o in observations if o['start']<end and o['end']>start]
            people=sorted({o['person_id'] for o in selected})
            return {'assetId':asset_id,'contentId':content,'title':asset['name'],'path':asset.get('relative_path',asset['name']),
                    'assetKind':asset.get('kind','video'),'identityBasis':'voice','speakerIds':people,'faceIds':[],'faceNames':[],'personIds':people,'personNames':[names[p] for p in people if names.get(p)]}
        poster=asset.get('poster_url','')
        docs.append(dict(visible(base(all_people=True),faces),id=asset_id+':file',kind='file',text=asset['name']+' '+asset.get('relative_path',''),seconds=0,image=poster,embed=False,source='file'))
        highlights=sorted(asset.get('highlights',[]),key=lambda h:float(h.get('seconds',h.get('start',0))))
        for i,h in enumerate(highlights):
            note=h.get('note',h.get('text','')).strip();start=float(h.get('seconds',h.get('start',0)))
            if not note:continue
            docs.append(dict(visible(base(start,voice_presence=False),[f for f in faces if f['frame_ref']==h.get('image_url',h.get('image','')) or abs(f['seconds']-start)<.02]),id=f'{asset_id}:visual:{i}',kind='visual',text=note,seconds=start,image=h.get('image_url',h.get('image','')),embed=True,source='ai_visual'))
        for face in faces:
            entity=face_entities.get(face['face_id'],{})
            docs.append(dict(visible(base(face['seconds'],voice_presence=False),[face]),id=f'{asset_id}:face:{face["observation_id"]}',kind='face',text=entity.get('name') or face['face_id'],seconds=face['seconds'],image=face['crop_ref'] or face['frame_ref'],embed=False,source='face_observation'))
        transcript=asset.get('transcript',[])
        if not isinstance(transcript,list):transcript=transcript.get('sentences',[])
        transcript=sorted([s for s in transcript if s.get('text','').strip()],key=lambda s:float(s.get('start',0)))
        for i,s in enumerate(transcript):
            start=float(s.get('start',0));end=float(s.get('end',start))
            for j,text in enumerate(_chunks(s['text'])):
                docs.append(dict(base(start,end),id=f'{asset_id}:speech:{i}:{j}',kind='speech',text=text,seconds=start,end=end,stream=s.get('stream'),image=poster,embed=True,source='ai_transcript'))
        for annotation in store.annotations(content):
            start=annotation['start'] or 0;end=annotation['end']
            # Only operator-entered values become search prose; provenance remains structured.
            text=annotation['text']
            if annotation['source']=='operator' and annotation['metadata']:
                text+=' '+_metadata_text(annotation['metadata'])
            elif annotation['source'] in ('accepted_inheritance','automatic_inheritance'):
                text+=' '+_metadata_text(annotation['metadata'].get('suggested_metadata',{}))
            for j,chunk in enumerate(_chunks(text)):
                docs.append(dict(base(start,end,annotation['start'] is None),id=f'{asset_id}:annotation:{annotation["id"]}:{j}',kind='operator',text=chunk,seconds=start,end=end,image=poster,embed=True,
                                 source=annotation['source'],annotationId=annotation['id'],provenance={'source_id':annotation['source_id'],'metadata':deepcopy(annotation['metadata'])}))
    return {'schema_version':1,'project_id':store.project_id,'edit_revision':store.edit_revision,'documents':docs}
