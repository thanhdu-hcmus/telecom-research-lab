"""Recompute saved seeded draws and check the protocol's shared-channel contract."""
from collections import defaultdict
from pathlib import Path
import csv
import numpy as np
from lab.io import load,save,now,sha256
from lab.simulation import validate_runs, verify_manifest, manifest_output

p=Path('projects/m11-noma-qos').resolve()
validate_runs(p)
reference={}
seeds=defaultdict(list)
checks=[]
failures=[]
for mf in sorted((p/'results/runs').glob('*/manifest.json')):
    m=verify_manifest(p,load(mf))
    if m.params['kind']=='deterministic':
        continue
    raw=manifest_output(p,m,'channels.csv')
    with raw.open(encoding='utf-8',newline='') as f:
        names=next(csv.reader(f))
    g=np.loadtxt(raw,delimiter=',',skiprows=1,usecols=(names.index('gw'),names.index('gs')))
    seed=m.seeds[0]
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,0])))
    recomputed=np.sort(rng.exponential(size=(m.params['trials'],2)),axis=1)
    reproducible=np.array_equal(recomputed,g)
    ordered=bool(np.all(g[:,0]<=g[:,1]))
    shared=seed not in reference or np.array_equal(reference[seed],g)
    if seed not in reference:
        reference[seed]=g
    seeds[seed].append(m.scenario)
    check={'run_id':m.run_id,'seed':seed,'scenario':m.scenario,
        'rows':len(g),'recomputed_identical':reproducible,
        'common_channels_identical':shared,'ordered_nonnegative':ordered and bool(np.all(g>=0)),
        'manifest_path':mf.relative_to(p).as_posix(),'manifest_sha256':sha256(mf)}
    checks.append(check)
    if not all([reproducible,shared,check['ordered_nonnegative']]):
        failures.append(m.run_id)
g=np.concatenate(list(reference.values()))
means=g.mean(axis=0)
expected=np.array([.5,1.5])
standard_errors=np.sqrt(np.array([.25,1.25])/len(g))
statistical_check=bool(np.all(np.abs(means-expected)<=5*standard_errors))
save(p/'results/channel-audit.json',{'timestamp':now(),
    'status':'PASS' if not failures and statistical_check else 'FAIL',
    'independent_seed_count':len(reference),'unique_blocks':len(g),
    'duplicate_grid_draws_not_independent':True,
    'expected_ordered_gain_means':expected.tolist(),'observed_ordered_gain_means':means.tolist(),
    'theoretical_standard_errors':standard_errors.tolist(),
    'moment_check':'Within five theoretical standard errors; finite sanity check only',
    'moment_check_passed':statistical_check,'failures':failures,'checks':checks})
print({'status':'PASS' if not failures and statistical_check else 'FAIL',
    'channel_jobs':len(checks),'unique_blocks':len(g),'observed_means':means.tolist()})
