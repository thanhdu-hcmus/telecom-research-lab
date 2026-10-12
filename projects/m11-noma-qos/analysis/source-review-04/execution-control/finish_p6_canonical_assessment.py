"""Wait for both reviewed operations, then run the reviewed combined assessor."""
import json,subprocess,sys,time,uuid
from pathlib import Path
from lab.io import load,save,sha256,now,within
sys.dont_write_bytecode=True
repo=Path.cwd();project=repo/'projects/m11-noma-qos';here=project/'analysis/supplement'
marker=repo/'.cache/p6-canonical-assessment-active.json';assert not marker.exists(),'Assessment watcher already exists'
folder=repo/'.cache/p6-canonical'/f'{uuid.uuid4().hex}-assessment';folder.mkdir(parents=True)
record=dict(status='WAITING',started=now(),directory=str(folder.relative_to(repo)),scientific_acceptance=False,numerical_external_review_launched=False)
save(marker,record);print(json.dumps(record),flush=True)
started=time.monotonic()
try:
 while True:
  steps={kind:load(repo/f'.cache/p6-canonical-{kind}-active.json') for kind in ['native','supplement']}
  if all(v['status']!='RUNNING' for v in steps.values()):break
  if time.monotonic()-started>92000:raise TimeoutError('Operations did not finish within watcher deadline')
  time.sleep(30)
 if any(v['status']!='RECORDED' for v in steps.values()):raise RuntimeError('One operation lacks a complete retained receipt')
 native=within(project,steps['native']['scientific_receipt']);supp=within(project,steps['supplement']['scientific_receipt'])
 assert native.name=='native-receipt.json' and supp.name=='execution-report.json'
 for kind,file in [('native',native),('supplement',supp)]:assert sha256(file)==steps[kind]['scientific_receipt_sha256']
 before={d.name for d in (here/'runs').glob('*') if d.is_dir()}
 command=[sys.executable,str(here/'checker.py'),'--assess',supp.relative_to(project).as_posix(),'--native-receipt',native.relative_to(project).as_posix()]
 record.update(status='ASSESSING',command=command,operations=steps);save(marker,record)
 with (folder/'stdout.txt').open('w',encoding='utf-8',newline='\n') as out,(folder/'stderr.txt').open('w',encoding='utf-8',newline='\n') as err:
  result=subprocess.run(command,cwd=repo,stdout=out,stderr=err,timeout=14400)
 candidates=[d for d in (here/'runs').glob('*') if d.is_dir() and d.name not in before and d.name.endswith('-assessment')]
 if len(candidates)!=1:raise RuntimeError('Cannot identify unique assessment output')
 file=candidates[0]/'combined-assessment.json';assessment=load(file)
 record.update(status='RECORDED',exit_code=result.returncode,assessment=file.relative_to(project).as_posix(),assessment_sha256=sha256(file),combined_status=assessment['status'],eligible_for_gate_request=assessment.get('eligible_for_gate_request',False),completed_jobs=steps['supplement'].get('jobs'),completed_rows=steps['supplement'].get('rows'))
except Exception as exc:record.update(status='INCOMPLETE',exception=type(exc).__name__+': '+str(exc))
finally:
 record.update(finished=now(),runtime_s=time.monotonic()-started,evidence={f.name:sha256(f) for f in folder.iterdir() if f.is_file()})
 save(folder/'assessment-operation-receipt.json',record);save(marker,record);print(json.dumps(record),flush=True)
