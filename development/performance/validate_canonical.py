"""Read-only canonical project validation; no model initialization or network."""
from pathlib import Path
import argparse,json,time
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path('/Volumes/ThunderBlade X8/Ingests'));p.add_argument('--require-upgrade',action='store_true');a=p.parse_args();project=a.project.resolve();notes=project/'_DIT_NOTES';before=json.loads((ROOT/'performance/canonical-before-upgrade.json').read_text());catalog=json.loads((notes/'catalog.json').read_text());assets=catalog['assets'];errors=[];counts={'assets':len(assets),'unique_content':len({x['content_id'] for x in assets}),'highlights':0,'transcript_segments':0,'face_observations':0};expected={x['content_id'] for x in before['catalog']['assets']}
 if {x['content_id'] for x in assets}!=expected:errors.append('Canonical content set changed')
 if len(assets)!=len(before['catalog']['assets']):errors.append('Canonical alias count changed')
 for path,stat in before['source_stats'].items():
  q=Path(path)
  if not q.is_file() or q.stat().st_size!=stat['size'] or q.stat().st_mtime_ns!=stat['mtime_ns']:errors.append('Source stat changed: '+path)
 def media_url(url):
  if url.startswith('/notes/'):
   target=(notes/url.removeprefix('/notes/')).resolve()
   if not target.is_relative_to(notes.resolve()) or not target.is_file():errors.append('Broken/unsafe evidence URL: '+url)
 for asset in assets:
  duration=asset['duration'];highlights=asset.get('highlights',[]);counts['highlights']+=len(highlights)
  for h in highlights:
   if not 0<=h.get('seconds',-1)<=duration:errors.append('Invalid highlight timestamp')
   if h.get('image_url'):media_url(h['image_url'])
  segments=asset.get('transcript',[]);counts['transcript_segments']+=len(segments)
  for s in segments:
   start=s.get('start',-1);end=s.get('end',-1)
   if not 0<=start<=end<=duration+.1:errors.append('Invalid transcript timestamp')
  for obs in asset.get('face_observations',asset.get('faces',[])):
   if isinstance(obs,dict):
    counts['face_observations']+=1
    for key in ['crop_url','image_url']:
     if obs.get(key):media_url(obs[key])
 seals={str(x.relative_to(notes)) for x in (notes/'.objects').glob('*/*/complete.json')};new=seals-set(before['sealed_before']);counts['new_sealed_objects']=len(new)
 if a.require_upgrade and len(new)<len(expected):errors.append('Not all unique inputs have a new sealed analysis profile')
 report={'checked_at':time.time(),'project':str(project),'passed':not errors,'counts':counts,'errors':errors,'scope':'Read-only structural/source-stat evidence check; face recall and semantic caption accuracy are not inferred.'};(ROOT/'benchmarks/canonical-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
