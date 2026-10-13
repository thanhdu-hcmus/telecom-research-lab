"""Full saved-row author diagnostic; excludes canonical guards/oracle/statistical acceptance."""
import csv,json,sys,time,uuid
from itertools import zip_longest
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';w=r/'.cache/worktrees/p6-crossing-r5';here=w/'projects/m11-noma-qos/analysis/supplement';sys.dont_write_bytecode=True;sys.path.insert(0,str(here))
from independent import Audit,check_row,seeded
marker=r/'.cache/p6-candidate-full-row-diagnostic-active.json';assert not marker.exists(),'Inspect existing diagnostic before any duplicate run'
d=r/'.cache/p6-full-candidate-audit'/uuid.uuid4().hex;d.mkdir(parents=True)
original=load(p/'analysis/source-review-ready.json')['source_hashes'];candidate=load(p/'analysis/P6-code-review-round5-payload.json')['source_hashes'];lock=load(p/'sim/lock.json')['input_hashes'];start=time.monotonic();records=[]
def stable():
 assert all(sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n)==h for n,h in original.items())
 assert all(sha256(w/n.removeprefix('@repo/') if n.startswith('@repo/') else w/'projects/m11-noma-qos'/n)==h for n,h in candidate.items())
 assert all(sha256(r/n)==h for n,h in lock.items())
stable();paths=sorted((p/'results/runs').glob('*/manifest.json'));assert len(paths)==145;cases=load(p/'sim/cases.yaml')['cases']
record=dict(status='RUNNING',started=now(),kind='LOCAL_AUTHOR_DIAGNOSTIC_ONLY',canonical_execution=False,scientific_acceptance=False,directory=d.relative_to(r).as_posix(),source_review_transmitted=False,planned_jobs=145,planned_rows=4718692)
save(marker,record);save(d/'launch.json',record)
try:
 with (d/'jobs.jsonl').open('w',encoding='utf-8',newline='\n') as log:
  for manifest in paths:
   m=load(manifest);params=m['params'];outputs={Path(o['path']).name:o for o in m['outputs']};files=[p/outputs[k]['path'] for k in ['channels.csv','metrics.csv']]
   for name,file in zip(['channels.csv','metrics.csv'],files):assert sha256(file)==outputs[name]['sha256'] and file.stat().st_size==outputs[name]['bytes']
   deterministic=params['kind']=='deterministic';gains=None if deterministic else seeded(m['seeds'][0],params['trials']);audit=Audit();rows=0;job_start=time.monotonic()
   with files[0].open(encoding='utf-8',newline='') as cf,files[1].open(encoding='utf-8',newline='') as mf:
    for i,(raw,metric) in enumerate(zip_longest(csv.DictReader(cf),csv.DictReader(mf))):
     assert raw is not None and metric is not None and i<params['trials']
     if deterministic:case=cases[i%len(cases)];inputs=list(map(float,case['values']));case_id=case['id']
     else:inputs=[params['P'],*map(float,gains[i]),params['qw'],params['qs']];case_id=''
     check_row(raw,metric,inputs,case_id,i,audit);rows+=1
     if i%1024==0 and (time.monotonic()-job_start>3600 or time.monotonic()-start>7200):raise TimeoutError('Author diagnostic budget exceeded; no scientific acceptance')
   assert rows==params['trials'];value=dict(run_id=m['run_id'],rows=rows,error_counts=audit.counts,errors=audit.errors,diagnostic_counts=audit.diagnostic_counts,ambiguities=audit.ambiguities,manifest_sha256=sha256(manifest),runtime_s=time.monotonic()-job_start)
   records.append(value);log.write(json.dumps(value,allow_nan=False)+'\n');log.flush();record.update(completed_jobs=len(records),completed_rows=sum(j['rows'] for j in records),errors=sum(sum(j['error_counts'].values()) for j in records));save(marker,record)
 stable();assert paths==sorted((p/'results/runs').glob('*/manifest.json'));assert sum(j['rows'] for j in records)==4718692
 record.update(status='COMPLETE',source_bindings_unchanged=True,locked_inputs_unchanged=True,finished=now(),runtime_s=time.monotonic()-start,limitations='Author check_row/seed regeneration diagnosis only; omits production integrity guards, shared oracle replay, global statistics, full canonical rerun and independent source/results review.')
except Exception as exc:record.update(status='INCOMPLETE',exception=type(exc).__name__+': '+str(exc),finished=now(),runtime_s=time.monotonic()-start)
finally:
 record['evidence']={f.name:sha256(f) for f in d.iterdir() if f.is_file()};save(d/'diagnostic-receipt.json',record);save(marker,record);print(json.dumps(record),flush=True)
sys.exit(0 if record['status']=='COMPLETE' else 2)
