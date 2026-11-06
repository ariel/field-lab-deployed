"""Reconcile without inference, verify complete coverage, and record test metrics."""
import json,sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
 from ditnotes.library import process,_valid_object
 from ditnotes.enrichment import publish_index
 from ditnotes.search_backend import SearchBackend
 from ditnotes.atomic import atomic_json
 from ditnotes.project_store import ProjectStore
 p=Path('/Users/mattb/Movies/BooshTest');n=p/'_DIT_NOTES';s=json.loads((p/'test-status.json').read_text())
 assert s['stage']=='complete',s['stage']
 started=time.time()
 r=process(p/'media',p,models_root=ROOT/'models',options={'interval':2,'max_frames':12,'timeout':1800})
 assert r['counts']=={'processed':0,'reused':30,'failed':0,'files':30},r
 backend=SearchBackend(ROOT,lambda e:None)
 try:index=publish_index(p,backend)
 finally:backend.close()
 catalog=json.loads((n/'catalog.json').read_text());assets=catalog['assets']
 assert len(assets)==30 and all(a['status']=='ready' for a in assets)
 duration=sum(a['duration'] for a in assets)
 def video_probe(path):
  probe=json.loads(subprocess.check_output([str(ROOT/'bin/ffprobe'),'-v','error','-select_streams','v:0','-show_entries','stream=duration,nb_frames','-of','json',str(path)]))
  return probe['streams'][0]
 original=video_probe(s['source']);videos=[video_probe(p/a['relative_path']) for a in assets]
 video_seconds=sum(float(v['duration']) for v in videos);video_frames=sum(int(v['nb_frames']) for v in videos)
 assert video_frames==int(original['nb_frames'])
 assert abs(video_seconds-float(original['duration']))<.1
 results=[];transcript=[];records=json.loads((n/'state.json').read_text())['paths']
 for i,a in enumerate(sorted(assets,key=lambda a:a['name'])):
  profile=records[a['relative_path']]['profile_id'];folder=n/'.objects'/a['content_id']/profile
  assert _valid_object(folder,a['content_id'],profile)
  result=json.loads((folder/'result.json').read_text());results.append(result)
  for sentence in a['transcript']:
   transcript.append({'start':sentence['start']+i*300,'end':sentence['end']+i*300,'text':sentence['text'],'part':a['relative_path']})
 atomic_json(p/'full-transcript.json',{'source':s['source'],'segments':transcript,'timestamp_basis':'original source seconds, nominal five-minute conversion boundaries'})
 elapsed=time.time()-s['started_at']
 with ProjectStore(n/'project.sqlite3',project_id=catalog['project']['id']) as store:
  named=[{'id':f['id'],'name':f['name']} for f in store.faces() if f.get('name') and not f.get('merged_into')]
 metrics={'status':'complete','source_seconds':s['source_duration'],'container_seconds_sum':duration,'video_seconds_sum':video_seconds,'video_frames':video_frames,'source_video_frames':int(original['nb_frames']),
          'conversion_note':'Container-duration sums include AAC packet padding/preroll at segment boundaries. Source-relative part offsets are nominal; video frame count and summed video duration match the original.',
          'parts':len(assets),'transcript_segments':len(transcript),'transcript_words':sum(len(t['text'].split()) for t in transcript),
          'visual_notes':sum(len(a['highlights']) for a in assets),'face_observations':sum(len(r['faces']['observations']) for r in results),
          'analysis_seconds_sum':sum(r['timing']['total_seconds'] for r in results),'pipeline_wallclock_seconds':s['elapsed'],'pipeline_wallclock_ratio':s['elapsed']/s['source_duration'],
          'test_session_seconds_including_interactive_debugging_and_validation':elapsed,
          'validation_seconds':time.time()-started,'resume_check':r['counts'],'index':index,'saved_face_names':named}
 atomic_json(p/'test-report.json',metrics);print(json.dumps(metrics,indent=2))

if __name__=='__main__':main()
