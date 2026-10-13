"""Author census and extra declared-policy replay; outside canonical acceptance."""
import csv
import importlib.util
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.simulation import verify_manifest

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/oracle-uncertainty-author-diagnostic'
d.mkdir(exist_ok=False)
ready=load(p/'analysis/source-review-ready.json');locks=load(p/'sim/lock.json')['input_hashes']
def stable():
    assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
    assert all(sha256(r/name)==digest for name,digest in locks.items())
stable()
manifest=p/'results/runs/r_deterministic-11999-250ccb4ad292-b2a7cf178_9d6f22bd59c7/manifest.json'
m=load(manifest);verify_manifest(p,m);outputs={Path(value['path']).name:value for value in m['outputs']}
channel=p/outputs['channels.csv']['path'];oracle_file=p/outputs['oracle.json']['path']
assert sha256(channel)==outputs['channels.csv']['sha256'] and sha256(oracle_file)==outputs['oracle.json']['sha256']
with channel.open(encoding='utf-8',newline='') as file:raw=list(csv.DictReader(file))
checks=load(oracle_file)['checks'];assert len(raw)==len(checks)==100
selected=[check for check in checks if check['oracle']['status']=='unresolved']
assert len(selected)==20
assert all(check['row']>=m['params']['sensitivity_rows'] and 'tighter_oracle' not in check for check in selected)
solver_path=p/'sim/src/oracle.py'
assert sha256(solver_path)==ready['source_hashes']['sim/src/oracle.py']
spec=importlib.util.spec_from_file_location('author_diagnostic_pinned_oracle',solver_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
policy={key:m['params'][key]/10 for key in ['rate_tolerance','split_tolerance','objective_tolerance']}
policy.update(max_root_iterations=96,max_optimizer_iterations=256)
records=[]
for check in selected:
    index=check['row'];row=raw[index];inputs=[float(row[key]) for key in ['P','gw','gs','qw','qs']]
    assert inputs==check['inputs']
    regenerated=module.solve(*inputs,**policy)
    normalized={key:None if isinstance(value,float) and math.isnan(value) else value for key,value in regenerated.items()}
    record=dict(row=index,case_id=row['case_id'],inputs=inputs,stored_analytic_status=check['analytic_status'],stored_base_oracle=check['oracle'],canonical_tighter_selected=False,additional_tighter_diagnostic=normalized)
    power,weak,strong,qw,qs=inputs
    if qw.is_integer() and qs.is_integer():
        A=Fraction.from_float(power)*Fraction.from_float(weak);B=Fraction.from_float(power)*Fraction.from_float(strong)
        low=Fraction(2**int(qs)-1)/B;high=(A-(2**int(qw)-1))/(A*2**int(qw))
        record['author_exact_domain']=dict(low=str(low),high=str(high),width=str(high-low),feasible=low<=high)
        if row['case_id']=='narrow-feasible':
            assert low<high and check['oracle']['exact_split']=='1/3' and high==Fraction(1,3)
            record['author_exact_domain']['witness_equals_approved_model_optimizer']=True
        elif row['case_id']=='narrow-infeasible':assert low>high
        elif row['case_id']=='large-finite-snr':
            assert B==2*A and A>1 and low<=high
            candidate=Fraction.from_float(check['oracle']['candidate_a'])
            assert low<=candidate<=high
            assert (1-candidate)*A>=1+candidate*A and candidate*B>=1
            # F(high)-F(candidate)=log2(1+z); ln(2)>=1/2 gives a rational upper bound.
            z=(A-1-2*candidate*A)/((1+A)*(1+2*candidate*A))
            bound=2*z;assert 0<=bound<Fraction.from_float(m['params']['objective_tolerance'])
            record['author_large_snr_objective_gap']=dict(candidate_exact_fraction=str(candidate),approved_model_optimizer=str(high),exact_log_argument_excess=str(z),rational_gap_upper_bound=str(bound),basis='log2(1+z)<=2*z because log(1+z)<=z and ln(2)>=1/2',below_declared_objective_tolerance=True,stored_oracle_gap_bound=check['oracle']['objective_gap_bound'],stored_oracle_optimality_status=check['oracle']['optimality_status'])
    records.append(record)
stable()
groups=Counter(record['case_id'] for record in records);assert groups==Counter({'narrow-feasible':5,'narrow-infeasible':5,'large-finite-snr':5,'fractional-boundary':5})
counts=Counter(record['additional_tighter_diagnostic']['status'] for record in records)
report=dict(timestamp=now(),status='AUTHOR_ONLY_UNCERTAINTY_CENSUS_AND_EXTRA_REPLAY',groups=dict(groups),stored_base_unresolved_rows=20,canonical_tighter_coverage_of_these_rows=0,additional_tighter_diagnostic_rows=20,additional_tighter_statuses=dict(counts),additional_tighter_policy=policy,canonical_replay_counts_unchanged=True,scientific_acceptance=False,stored_labels_changed=False,source_and_locked_inputs_unchanged=True,records=records,evidence=dict(manifest=manifest.relative_to(p).as_posix(),manifest_sha256=sha256(manifest),channels=channel.relative_to(p).as_posix(),channels_sha256=sha256(channel),oracle=oracle_file.relative_to(p).as_posix(),oracle_sha256=sha256(oracle_file),solver='sim/src/oracle.py',solver_sha256=sha256(solver_path),model='model/model-spec.tex',model_sha256=sha256(p/'model/model-spec.tex')),limits=['Additional calls use the same pinned shared oracle; this is not a third independent optimizer.','The twenty extra tighter checks are author diagnostics, excluded from canonical4708base/1160tighter replay coverage and acceptance.','Exact-domain and objective-gap deductions are author certificates awaiting independent results review.','No locked source/model/protocol, tolerance, stored result, scientific gate or deviation is changed.'])
save(d/'census.json',report)
md='''# Author census of remaining oracle uncertainty

The saved deterministic oracle has twenty unresolved base checks: four cases,
each repeated five times. The canonical tighter policy covers rows0-7; all
twenty unresolved rows occur later, so none has a canonical tighter replay.

| Case | Repeats | Base-oracle uncertainty | Exact author observation |
|---|---:|---|---|
| narrow-feasible | 5 | Feasible witness found; maximum unresolved in narrow interval | The stored exact witness1/3 equals the approved model's maximizing upper endpoint. |
| narrow-infeasible | 5 | Narrow domain lacks an oracle certificate | Exact rational lower bound exceeds the upper bound. |
| large-finite-snr | 5 | Numerical concavity gap exceeds tolerance | The stored candidate is exactly feasible and its model-derived rational objective-gap bound is below the declared tolerance. |
| fractional-boundary | 5 | Noninteger singleton lacks a direct oracle certificate | The separate author certificate derives sqrt(2)-1; saved labels stay unresolved. |

## Additional local replay

The same pinned oracle was called on these twenty saved inputs using the
existing tenfold tighter tolerances and unchanged96/256iteration caps.
These calls are extra author diagnostics. Canonical coverage remains
4,708base and1,160tighter calls. Actual returned statuses are in census.json.

## Large-SNR gap deduction

For A=P*g_w, B=2*A, q_w=q_s=1, the approved real-model optimum is
u=(A-1)/(2*A). For the stored exactly feasible candidate c, let
z=(A-1-2*c*A)/((1+A)*(1+2*c*A)). Direct substitution gives
F(u)-F(c)=log2(1+z). Since log(1+z)<=z and ln(2)>=1/2,
the nonnegative gap is at most2*z. Exact Fraction arithmetic checks
2*z against the actual declared objective tolerance for all five repeats.
The saved numerical oracle's loose gap bound still remains not-established.

These deductions explain uncertainty without changing runtime acceptance.
The canonical run, stored labels, source/model/protocol and PI gates remain
unchanged. Independent numerical-results review remains pending.
'''
md+=f"\nExtra tighter status counts: {json.dumps(dict(counts))}.\n"
(d/'census.md').write_text(md,encoding='utf-8',newline='\n')
print(json.dumps(dict(status=report['status'],groups=dict(groups),extra_tighter_statuses=dict(counts),canonical_counts_unchanged=True)))
