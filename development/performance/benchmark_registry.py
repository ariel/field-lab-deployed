#!/usr/bin/env python3
"""CPU-only project-store scaling, synthetic embeddings; not voice quality."""
import json,sys,tempfile,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lab_indexer.project_store import ProjectStore
rng=np.random.default_rng(281);results=[]
for count in (25,100):
 with tempfile.TemporaryDirectory(prefix='registry-bench-',dir=ROOT/'benchmarks') as directory:
  vectors=rng.normal(size=(count,192));vectors/=np.linalg.norm(vectors,axis=1,keepdims=True)
  with ProjectStore(Path(directory)/'project.sqlite3') as store:
   people=[]
   for i,vector in enumerate(vectors):people.append(store.assign_speaker(f'seed-{i}','0',0,6,vector.tolist(),'synthetic192-v1',1.,auto_assign=False)['person_id'])
   times=[]
   for i in range(20):
    started=time.perf_counter();row=store.assign_speaker(f'probe-{i}','0',0,6,vectors[0].tolist(),'synthetic192-v1',1.,auto_assign=True);times.append(time.perf_counter()-started)
    assert row['person_id']==people[0]
   results.append({'profiles':count,'probes':20,'median_seconds':float(np.median(times)),'max_seconds':max(times),'note':'Synthetic unit vectors measure registry/SQLite cost only; these are not voice embeddings or accuracy evidence.'})
report={'runs':results};(ROOT/'benchmarks/registry_cpu.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
