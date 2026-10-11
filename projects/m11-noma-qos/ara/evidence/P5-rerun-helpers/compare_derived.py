"""Compare freshly recomputed numerical fields, with declared provenance exclusions."""
import csv
from pathlib import Path
from lab.io import load, save, now, sha256

p=Path('projects/m11-noma-qos')
a=p/'archive/2026-10-11T16-51-50.467789+00-00'
comparison=load(p/'ara/staging/P5-rerun-output-comparison.json')
assert comparison['status']=='PASS'
mapping={j['old_run_id']:j['new_run_id'] for j in comparison['jobs']}
checks=[]
old,new=load(a/'results/statistics.json'),load(p/'results/statistics.json')
for value in [old,new]:
    value.pop('input_manifest_hashes')
    for row in value['scenarios']:
        row.pop('runtime_s')
assert old==new,'Fresh scientific/statistical fields differ'
checks.append({'artifact':'statistics.json','numerical_fields_match':True,
               'excluded':['input_manifest_hashes','scenarios[].runtime_s']})
old,new=load(a/'results/diagnostics.json'),load(p/'results/diagnostics.json')
for value in [old,new]:
    for name in ['timestamp','job_details','total_job_runtime_s']:
        value.pop(name)
for row in old['unresolved']:
    row['run_id']=mapping[row['run_id']]
for row in old['disagreements']:
    row['run_id']=mapping[row['run_id']]
assert old==new,'Fresh oracle diagnostic values differ'
checks.append({'artifact':'diagnostics.json','numerical_fields_match':True,
               'excluded':['timestamp','job_details (new run lineage and measured runtime)','total_job_runtime_s'],
               'mapping':'Archived unresolved/disagreement run IDs mapped through full output comparison'})
old,new=load(a/'results/channel-audit.json'),load(p/'results/channel-audit.json')
for value in [old,new]:
    value.pop('timestamp')
    for row in value['checks']:
        for name in ['run_id','manifest_path','manifest_sha256']:
            row.pop(name)
    value['checks'].sort(key=lambda x:(x['scenario'],x['seed']))
assert old==new,'Fresh seeded-channel audit values differ'
checks.append({'artifact':'channel-audit.json','numerical_fields_match':True,
               'excluded':['timestamp','checks[].run_id','checks[].manifest_path','checks[].manifest_sha256'],
               'order':'Checks compared by scenario and seed'})
def summary(root):
    with (root/'results/summary.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==145
    result={}
    for row in rows:
        row.pop('run_id')
        key=(row['scenario'],row['seed'])
        assert key not in result
        result[key]=row
    return result
assert summary(a)==summary(p),'Fresh native raw-metric summary differs'
checks.append({'artifact':'summary.csv','numerical_fields_match':True,'excluded':['run_id'],
               'method':'Exact remaining CSV field strings, matched by scenario/seed; NaN markers retained'})
for cache,evidence in [('.cache/p5_analyze_checks.py','ara/evidence/P5-rerun-helpers/diagnostics.py'),
                       ('.cache/p5_channel_audit.py','ara/evidence/P5-rerun-helpers/channel_audit.py'),
                       ('.cache/p5_rerun_pipeline.py','ara/evidence/P5-rerun-helpers/pipeline.py')]:
    assert sha256(Path(cache))==sha256(p/evidence),cache
save(p/'ara/staging/P5-rerun-derived-comparison.json',{
    'timestamp':now(),'status':'PASS','checks':checks,
    'method':'Compare fresh computations with archived R1, excluding only declared run provenance and measured runtime fields. All raw output bytes were separately read and matched. This is author reproducibility evidence, not independent P6 verification.',
    'source_copies_match_executed_helpers':True,
    'files':{str(root/name):sha256(root/name) for root in [a,p]
             for name in ['results/statistics.json','results/diagnostics.json','results/channel-audit.json','results/summary.csv']}})
print({'status':'PASS','fresh_derived_artifacts_match':4,'retained_helper_sources_match':3})
