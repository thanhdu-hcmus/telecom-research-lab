"""Prepare/request fresh G5 only when ordinary P5 recomputation succeeds."""
import subprocess
import sys
import time
from pathlib import Path
from lab.io import load, save, now, sha256
from lab.state import decisions

repo=Path.cwd().resolve()
p=repo/'projects/m11-noma-qos'
receipt=p/'ara/staging/P5-rerun-recomputation.json'
progress=repo/'.cache/m11-p5-rerun-gate-progress.json'
save(progress,{'status':'waiting for fresh raw recomputation','timestamp':now()})
while not receipt.exists():
    time.sleep(3)
v=load(receipt)
assert v['status']=='PASS'
for x in v['commands'].values():
    assert x['status']=='PASS' and x['exit_code']==0
    print(x['stdout']+': '+(repo/x['stdout']).read_text(encoding='utf-8').strip(),flush=True)
collect=load(repo/v['commands']['collect']['stdout'])
assert collect['status']=='PASS' and collect['rows']==145
before=decisions(p)
subprocess.run([sys.executable,str(repo/'.cache/p5_rerun_report.py')],cwd=repo,check=True)
save(progress,{'status':'native G5 validation/request running','timestamp':now()})
out=repo/'.cache/m11-p5-rerun-gate-request.json'
err=repo/'.cache/m11-p5-rerun-gate-request.stderr.txt'
with out.open('w',encoding='utf-8') as oh,err.open('w',encoding='utf-8') as eh:
    result=subprocess.run([str(repo/'.venv/Scripts/lab.exe'),'gate','request','G5','--project','m11-noma-qos','--json'],cwd=repo,stdout=oh,stderr=eh)
v=load(out)
assert result.returncode==0 and v['status']=='PASS',v
assert decisions(p)==before,'Gate request must not create a PI decision'
subprocess.run([sys.executable,str(repo/'.cache/p5_rerun_finalize.py')],cwd=repo,check=True)
save(p/'ara/staging/P5-rerun-gate-request.json',{
    'timestamp':now(),'status':'PASS','native_request':v,
    'local_stdout':out.relative_to(repo).as_posix(),'stdout_sha256':sha256(out),
    'stderr_sha256':sha256(err),'scientific_decision_added':False,
    'G5':'pending; PI decision required','G6_G7':'invalidated'})
save(progress,{'status':'PASS; fresh G5 pending PI review','timestamp':now()})
print({'gate_request':'PASS','G5':'pending; no PI decision performed'},flush=True)
