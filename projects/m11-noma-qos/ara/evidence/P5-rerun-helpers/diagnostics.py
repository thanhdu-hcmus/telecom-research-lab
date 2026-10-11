"""Synthesize the locked protocol's declared oracle diagnostics, without reruns."""
from collections import Counter, defaultdict
from pathlib import Path
import math
from lab.io import load, save, now
from lab.simulation import validate_runs, verify_manifest, manifest_output

p=Path('projects/m11-noma-qos').resolve()
validate_runs(p)
cases=load(p/'sim/cases.yaml')['cases']
statuses=Counter()
tighter_statuses=Counter()
reasons=Counter()
disagreements=[]
uncertain=[]
rate_errors=[]
split_errors=[]
gap_bounds=[]
tighter_errors=[]
jobs=[]
for mf in sorted((p/'results/runs').glob('*/manifest.json')):
    m=verify_manifest(p, load(mf))
    data=load(manifest_output(p,m,'oracle.json'))
    for c in data['checks']:
        o=c['oracle']
        statuses[o['status']]+=1
        reason=o['reason']
        if o['status']=='unresolved':
            reasons[reason]+=1
            uncertain.append({'run_id':m.run_id,'row':c['row'],
                'case_id':cases[c['row']%20]['id'] if m.scenario=='deterministic' else None,
                'analytic_status':c['analytic_status'],'oracle_status':o['status'],
                'reason':reason,'exact_split':o.get('exact_split'),
                'feasibility_certificate':o['feasibility_certificate'],
                'inputs':c['inputs']})
        if o['status']!='unresolved' and c['analytic_status']!='unresolved' and o['status']!=c['analytic_status']:
            disagreements.append({'run_id':m.run_id,'row':c['row'],'inputs':c['inputs'],
                                  'analytic':c['analytic_status'],'oracle':o['status']})
        if o.get('sum_rate') is not None and c['analytic_sum'] is not None:
            error=abs(o['sum_rate']-c['analytic_sum'])
            rate_errors.append(error)
            if error>1e-7:
                disagreements.append({'run_id':m.run_id,'row':c['row'],'objective_error':error})
        if o.get('objective_gap_bound') is not None:
            gap_bounds.append(o['objective_gap_bound'])
        tighter=c.get('tighter_oracle')
        if tighter:
            tighter_statuses[tighter['status']]+=1
            if o.get('sum_rate') is not None and tighter.get('sum_rate') is not None:
                tighter_errors.append(abs(o['sum_rate']-tighter['sum_rate']))
    jobs.append({'run_id':m.run_id,'scenario':m.scenario,'seed':m.seeds[0],
        'runtime_s':m.runtime_s,'raw_bytes':sum(x.bytes for x in m.outputs if x.path.endswith('.csv')),
        'start':m.start,'end':m.end})
value={'timestamp':now(),'status':'diagnostics computed; independent P6 verification pending',
    'jobs':len(jobs),'oracle_checks':sum(statuses.values()),'oracle_status_counts':dict(statuses),
    'tighter_status_counts':dict(tighter_statuses),'unresolved_reasons':dict(reasons),
    'disagreements':disagreements,'unresolved':uncertain,
    'maximum_objective_agreement_error':max(rate_errors,default=None),
    'maximum_numerical_objective_gap':max(gap_bounds,default=None),
    'maximum_tighter_objective_difference':max(tighter_errors,default=None),
    'total_job_runtime_s':sum(x['runtime_s'] for x in jobs),
    'raw_csv_bytes':sum(x['raw_bytes'] for x in jobs),
    'job_details':jobs,
    'limitations':'Numerical secant gap is not rigorous interval arithmetic. Unresolved statuses retained; finite checks are not universal proofs.'}
save(p/'results/diagnostics.json',value)
print({k:value[k] for k in ['jobs','oracle_checks','oracle_status_counts','tighter_status_counts',
    'maximum_objective_agreement_error','maximum_tighter_objective_difference','total_job_runtime_s','raw_csv_bytes']})
print({'disagreements':len(disagreements),'unresolved_reasons':dict(reasons)})
