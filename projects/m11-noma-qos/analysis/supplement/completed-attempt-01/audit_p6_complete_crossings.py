"""Local diagnosis of crossing errors in completed jobs, never canonical acceptance."""
import csv,hashlib,json,math,time
from collections import Counter
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';start=time.monotonic()
ready=load(p/'analysis/source-review-ready.json');before={n:sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n) for n in ready['source_hashes']}
lock=load(p/'sim/lock.json');assert all(sha256(r/n)==h for n,h in lock['input_hashes'].items())
stream=p/'analysis/supplement/runs/2026-10-12T15-09-58.183477+00-00-6aacbf54576d4d638666b082e5ae374d-supplement/execution.jsonl'
jobs=[json.loads(line) for line in stream.read_text().splitlines() if line.strip()];results=[];examples=[];row_snapshots=[]
for job in jobs:
 if not job['row_error_count']:continue
 d=p/'results/runs'/job['run_id'];m=load(d/'manifest.json');path=d/'channels.csv';o=next(o for o in m['outputs'] if o['path'].endswith('/channels.csv'));assert sha256(path)==o['sha256']
 old=Counter();stable=Counter();outside=Counter();max_ratio=0.;rows=0
 with path.open(encoding='utf-8',newline='') as f:
  for raw in csv.DictReader(f):
   rows+=1
   for field,x,q,inc in [('interval_lower',float(raw['B']),float(raw['qs']),True),('interval_upper',float(raw['A']),float(raw['qw']),False)]:
    if x==0 or q==0 or q.is_integer():continue
    t=math.expm1(q*math.log(2));f0=-t if inc else x-t;f1=x-t if inc else -t*(1+x)
    previous=-f0/(f1-f0);corrected=t/x if inc else (x-t)/(x*(1+t))
    if not inc:previous=min(1.,previous);corrected=min(1.,corrected)
    actual=float(raw[field])
    if abs(actual-previous)>1e-12:old[field]+=1
    if abs(actual-corrected)>1e-12:
     stable[field]+=1;out=(actual<0 and corrected<0) or (actual>1 and corrected>1)
     if out:outside[field]+=1
     ratio=abs(actual-corrected)/math.ulp(max(1.,abs(actual),abs(corrected)));max_ratio=max(max_ratio,ratio)
     if len(examples)<10:
      examples.append(dict(run_id=job['run_id'],row=int(raw['row']),field=field,stored=actual,stable=corrected,error=abs(actual-corrected),ulp_count=ratio,both_same_outside_domain=out,status=raw['status']))
      row_snapshots.append(dict(run_id=job['run_id'],raw=raw))
 assert rows==job['rows']
 results.append(dict(run_id=job['run_id'],rows=rows,recorded_errors=job['row_error_count'],old_crossing_errors=dict(old),old_crossing_errors_explain_entire_job=sum(old.values())==job['row_error_count'],stable_crossing_errors=dict(stable),same_outside_domain_errors=dict(outside),max_stable_difference_in_ulps=max_ratio,manifest_sha256=sha256(d/'manifest.json'),channels_sha256=o['sha256']))
 print(json.dumps(dict(job=len(results),run_id=job['run_id'],old=sum(old.values()),stable=sum(stable.values()),recorded=job['row_error_count'])),flush=True)
assert all(sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n)==h for n,h in before.items());assert all(sha256(r/n)==h for n,h in lock['input_hashes'].items())
report=dict(timestamp=now(),kind='LOCAL_DIAGNOSTIC_ONLY',completed_job_snapshot=len(jobs),jobs_with_recorded_errors=len(results),recorded_errors=sum(j['row_error_count'] for j in jobs),old_crossing_errors=sum(sum(j['old_crossing_errors'].values()) for j in results),stable_crossing_errors=sum(sum(j['stable_crossing_errors'].values()) for j in results),entire_recorded_error_count_explained=all(j['old_crossing_errors_explain_entire_job'] for j in results),sources_unchanged=True,locked_inputs_unchanged=True,reviewed_source_hashes=before,rows_with_error_jobs=sum(j['rows'] for j in results),runtime_s=time.monotonic()-start,jobs=results,samples=examples,limitation='Crossing-field diagnosis only, for a snapshot of completed error-bearing jobs; no scientific acceptance, full independent rerun or canonical guard replacement.')
save(r/'.cache/p6-complete-crossing-diagnosis.json',report);save(r/'.cache/p6-complete-crossing-regression-rows.json',row_snapshots);print(json.dumps({k:v for k,v in report.items() if k not in ['jobs','samples','reviewed_source_hashes']}))
