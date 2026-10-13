"""Capture one canonical reviewed operation without replacing native guards."""
import json,subprocess,sys,time,uuid
from pathlib import Path
from lab.io import load,save,sha256,now
sys.dont_write_bytecode=True
repo=Path.cwd();project=repo/'projects/m11-noma-qos';here=project/'analysis/supplement'
assert len(sys.argv)==2 and sys.argv[1] in ['--native','--execute']
operation=sys.argv[1];kind='native' if operation=='--native' else 'supplement'
ready=load(project/'analysis/source-review-ready.json');assert ready['recommendation']=='ready' and ready['enforced_independent_review'] and ready['review_round']==5
for name,digest in ready['source_hashes'].items():assert sha256(repo/name.removeprefix('@repo/') if name.startswith('@repo/') else project/name)==digest
marker=repo/f'.cache/p6-canonical-attempt2-{kind}-active.json';assert not marker.exists(),'Canonical step already launched; retain evidence and inspect before any retry'
directory=repo/'.cache/p6-canonical-attempt2'/f'{uuid.uuid4().hex}-{kind}';directory.mkdir(parents=True)
before={p.name for p in (here/'runs').glob('*') if p.is_dir()}
command=[sys.executable,str(here/'checker.py'),operation]
record=dict(status='RUNNING',attempt=2,review_round=5,kind=kind,started=now(),command=command,directory=str(directory.relative_to(repo)),source_ready_sha256=sha256(project/'analysis/source-review-ready.json'),canonical_execution_requested=True,scientific_acceptance=False)
save(marker,record);save(directory/'launch.json',record);print(json.dumps(record),flush=True)
start=time.monotonic()
try:
 with (directory/'stdout.txt').open('w',encoding='utf-8',newline='\n') as out,(directory/'stderr.txt').open('w',encoding='utf-8',newline='\n') as err:
  process=subprocess.Popen(command,stdout=out,stderr=err,cwd=repo)
  record['pid']=process.pid;save(marker,record)
  try:code=process.wait(timeout=14400 if kind=='native' else 90000)
  except subprocess.TimeoutExpired:
   process.terminate();process.wait(timeout=60)
   record.update(status='INCOMPLETE',exception='Outer operation deadline exceeded; command terminated; existing scientific receipts/logs retained')
   code=None
 record['exit_code']=code
 candidates=[p for p in (here/'runs').glob('*') if p.is_dir() and p.name not in before and p.name.endswith('-'+kind)]
 name='native-receipt.json' if kind=='native' else 'execution-report.json'
 if len(candidates)!=1 or not (candidates[0]/name).is_file():raise RuntimeError('Cannot identify exactly one completed operation receipt')
 receipt=candidates[0]/name;value=load(receipt)
 record.update(status='RECORDED',scientific_receipt=receipt.relative_to(project).as_posix(),scientific_receipt_sha256=sha256(receipt),scientific_status=value['status'],jobs=len(value.get('jobs',[])),rows=sum(j.get('rows',0) for j in value.get('jobs',[])))
except Exception as exc:record.update(status='INCOMPLETE',exception=type(exc).__name__+': '+str(exc))
finally:
 record.update(finished=now(),runtime_s=time.monotonic()-start,evidence={p.name:sha256(p) for p in directory.iterdir() if p.is_file()})
 save(directory/'operation-receipt.json',record);save(marker,record);print(json.dumps(record),flush=True)
sys.exit(0 if record['status']=='RECORDED' else 2)
