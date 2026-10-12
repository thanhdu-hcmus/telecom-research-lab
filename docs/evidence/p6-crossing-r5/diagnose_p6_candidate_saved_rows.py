"""Author diagnostic against saved rows; not a canonical supplemental execution."""
import csv,json,sys,time
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';w=r/'.cache/worktrees/p6-crossing-r5';candidate=w/'projects/m11-noma-qos/analysis/supplement'
sys.dont_write_bytecode=True;sys.path.insert(0,str(candidate))
from independent import Audit,check_row,seeded,METRIC_COLUMNS
names=['r_mc-00-q1-11001-250ccb4ad292-b2a7cf17890b_5f23c8954129','r_mc-00-q2-11001-250ccb4ad292-b2a7cf17890b_bdd256e32670']
# Select a real completed fractional-q2 manifest without guessing its run suffix.
q2=sorted((p/'results/runs').glob('r_mc-00-q2-11001*/manifest.json'));assert len(q2)==1;names[1]=q2[0].parent.name
sources={f.name:sha256(f) for f in candidate.glob('*.py')};results=[];start=time.monotonic()
for name in names:
 d=p/'results/runs'/name;m=load(d/'manifest.json');paths=[d/'channels.csv',d/'metrics.csv']
 for file in paths:
  o=next(o for o in m['outputs'] if o['path'].endswith('/'+file.name));assert sha256(file)==o['sha256']
 a=Audit();params=m['params'];gains=seeded(m['seeds'][0],params['trials']);rows=0
 with paths[0].open(encoding='utf-8',newline='') as cf,paths[1].open(encoding='utf-8',newline='') as mf:
  for i,(raw,metric) in enumerate(zip(csv.DictReader(cf),csv.DictReader(mf))):
   inputs=[params['P'],*map(float,gains[i]),params['qw'],params['qs']]
   check_row(raw,metric,inputs,'',i,a);rows+=1
 assert rows==params['trials'];results.append(dict(run_id=name,rows=rows,error_counts=a.counts,errors=a.errors,diagnostic_counts=a.diagnostic_counts,ambiguities=a.ambiguities,manifest_sha256=sha256(d/'manifest.json'),channels_sha256=sha256(paths[0]),metrics_sha256=sha256(paths[1])))
 print(json.dumps(dict(run_id=name,rows=rows,error_counts=a.counts,diagnostic_counts=a.diagnostic_counts)),flush=True)
assert sources=={f.name:sha256(f) for f in candidate.glob('*.py')}
ready=load(p/'analysis/source-review-ready.json');assert all(sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n)==h for n,h in ready['source_hashes'].items())
assert all(sha256(r/n)==h for n,h in load(p/'sim/lock.json')['input_hashes'].items())
report=dict(timestamp=now(),kind='LOCAL_AUTHOR_DIAGNOSTIC_ONLY',canonical_execution=False,scientific_acceptance=False,rows=sum(j['rows'] for j in results),candidate_source_hashes=sources,candidate_sources_unchanged=True,canonical_reviewed_sources_unchanged=True,locked_inputs_unchanged=True,results=results,runtime_s=time.monotonic()-start,scope='check_row and seeded-channel regeneration for two completed saved jobs; excludes shared oracle replay, global statistics, combined assessment and canonical production guards.')
save(r/'.cache/p6-candidate-saved-row-diagnostic.json',report)
