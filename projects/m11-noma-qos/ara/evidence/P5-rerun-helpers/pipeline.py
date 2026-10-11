"""Fresh P5 output comparison and ordinary guarded recomputation, no gate decisions."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import subprocess
import sys
import time

from lab.io import load, now, save, sha256

repo = Path.cwd().resolve()
p = repo / 'projects/m11-noma-qos'
archive = p / 'archive/2026-10-11T16-51-50.467789+00-00'
receipt = repo / '.cache/m11-p5-rerun-run.json'
progress = repo / '.cache/m11-p5-rerun-postprocessing.json'

while True:
    try:
        run = json.loads(receipt.read_text(encoding='utf-8-sig'))
        break
    except (FileNotFoundError, json.JSONDecodeError):
        time.sleep(3)
assert run['status'] == 'PASS', run
assert len(run['jobs']) == 145
assert not any(j['resumed'] for j in run['jobs'])

def jobs(root):
    result = {}
    for f in sorted((root / 'results/runs').glob('*/manifest.json')):
        m = load(f)
        key = (m['scenario'], tuple(m['seeds']))
        assert key not in result, key
        result[key] = (f, m)
    return result

old, new = jobs(archive), jobs(p)
assert len(old) == len(new) == 145 and old.keys() == new.keys()
lock_old, lock_new = load(archive/'sim/lock.json'), load(p/'sim/lock.json')
assert lock_old['protocol_hash'] == lock_new['protocol_hash']
changed = sorted(k for k in set(lock_old['input_hashes']) | set(lock_new['input_hashes'])
                 if lock_old['input_hashes'].get(k) != lock_new['input_hashes'].get(k))
assert changed == ['lab/verification.py'], changed
details = []
differences = []
output_count = 0
total_bytes = 0
for key in sorted(new):
    old_file, om = old[key]
    new_file, nm = new[key]
    for field in ('scenario', 'params', 'seeds', 'language', 'env', 'host', 'protocol_hash', 'status'):
        assert om[field] == nm[field], (key, field)
    assert om['input_hashes'] == lock_old['input_hashes']
    assert nm['input_hashes'] == lock_new['input_hashes']
    assert om['protocol_commit'] == lock_old['protocol_commit']
    assert nm['protocol_commit'] == lock_new['protocol_commit']
    outputs_old = {Path(o['path']).name:o for o in om['outputs']}
    outputs_new = {Path(o['path']).name:o for o in nm['outputs']}
    assert len(outputs_old) == len(om['outputs']) == 7
    assert len(outputs_new) == len(nm['outputs']) == 7
    assert outputs_old.keys() == outputs_new.keys()
    outputs = []
    for name in sorted(outputs_new):
        oo, no = outputs_old[name], outputs_new[name]
        assert oo['storage'] == no['storage'] == 'project'
        of, nf = archive/oo['path'], p/no['path']
        oh, nh = sha256(of), sha256(nf)
        assert oh == oo['sha256'] and of.stat().st_size == oo['bytes'], of
        assert nh == no['sha256'] and nf.stat().st_size == no['bytes'], nf
        identical = oh == nh and oo['bytes'] == no['bytes']
        outputs.append({'filename':name, 'old_path':of.relative_to(repo).as_posix(),
                        'new_path':nf.relative_to(repo).as_posix(), 'old_sha256':oh,
                        'new_sha256':nh, 'old_bytes':oo['bytes'], 'new_bytes':no['bytes'],
                        'both_manifest_bindings_match':True, 'byte_identical':identical})
        if not identical:
            differences.append({'scenario':key[0], 'seeds':list(key[1]), 'filename':name})
        output_count += 1
        total_bytes += no['bytes']
    details.append({'scenario':key[0], 'seeds':list(key[1]), 'old_run_id':om['run_id'],
                    'new_run_id':nm['run_id'], 'old_manifest_sha256':sha256(old_file),
                    'new_manifest_sha256':sha256(new_file), 'outputs':outputs})
comparison = {'timestamp':now(), 'status':'PASS' if not differences else 'FAIL',
              'method':'Read and SHA256 actual archived and fresh output bytes, verify each manifest size/hash, then compare by scenario/seed/filename. This engineering reproducibility check is not independent P6 scientific verification.',
              'fresh_native_run_status':run['status'], 'fresh_jobs':145, 'resumed_jobs':0,
              'physical_protocol_unchanged':True, 'changed_locked_inputs':changed,
              'old_protocol_commit':lock_old['protocol_commit'], 'new_protocol_commit':lock_new['protocol_commit'],
              'protocol_hash':lock_new['protocol_hash'], 'output_files_compared':output_count,
              'bytes_per_generation':total_bytes, 'environment_and_parameters_match':True,
              'differences':differences, 'jobs':details}
save(p/'ara/staging/P5-rerun-output-comparison.json', comparison)
print(json.dumps({k:comparison[k] for k in ('status','fresh_jobs','output_files_compared','differences')}), flush=True)
assert not differences, 'Numerical reproducibility difference retained in comparison receipt'

# Each program retains its ordinary immutable protocol and per-manifest guards.
# No validation caching, monkeypatching, or transportation of old summaries.
commands = {
    'collect':[str(repo/'.venv/Scripts/lab.exe'),'sim','collect','--project','m11-noma-qos','--json'],
    'aggregate':[sys.executable,str(p/'sim/src/aggregate.py'),'--project',str(p)],
    'diagnostics':[sys.executable,str(repo/'.cache/p5_analyze_checks.py')],
    'channels':[sys.executable,str(repo/'.cache/p5_channel_audit.py')],
}
active = {}
state = {'started_at':now(), 'status':'running', 'commands':{}}
for name, command in commands.items():
    out = repo/f'.cache/m11-p5-rerun-{name}.stdout.txt'
    err = repo/f'.cache/m11-p5-rerun-{name}.stderr.txt'
    oh, eh = out.open('w',encoding='utf-8'), err.open('w',encoding='utf-8')
    process = subprocess.Popen(command,cwd=repo,stdout=oh,stderr=eh)
    active[name] = (process,oh,eh)
    state['commands'][name] = {'command':command, 'pid':process.pid, 'status':'running',
                               'stdout':out.relative_to(repo).as_posix(), 'stderr':err.relative_to(repo).as_posix()}
save(progress,state)
while active:
    for name, (process,oh,eh) in list(active.items()):
        code = process.poll()
        if code is not None:
            oh.close(); eh.close()
            state['commands'][name].update(status='PASS' if code == 0 else 'FAIL', exit_code=code, ended_at=now())
            print(json.dumps({'command':name, 'exit_code':code}),flush=True)
            del active[name]
            save(progress,state)
    if active:
        time.sleep(5)
state.update(status='PASS' if all(v['exit_code']==0 for v in state['commands'].values()) else 'FAIL', ended_at=now())
save(progress,state)
save(p/'ara/staging/P5-rerun-recomputation.json', {
    **state, 'method':'Fresh raw-output recomputation with each original program and all native lock/manifest checks enabled.',
    'raw_comparison_receipt_sha256':sha256(p/'ara/staging/P5-rerun-output-comparison.json'),
    'logs':{v[k]:sha256(repo/v[k]) for v in state['commands'].values() for k in ('stdout','stderr')},
    'independent_P6_verification':False})
print(json.dumps({'postprocessing':state['status']}),flush=True)
sys.exit(state['status']!='PASS')
