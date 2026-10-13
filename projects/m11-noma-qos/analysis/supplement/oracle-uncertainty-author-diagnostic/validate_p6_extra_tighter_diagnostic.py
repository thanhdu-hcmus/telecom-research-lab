import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from lab.io import load,save,sha256,now

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/oracle-uncertainty-author-diagnostic'
report=load(d/'census.json');validated=[]
by_case={case:dict(Counter(row['additional_tighter_diagnostic']['status'] for row in report['records'] if row['case_id']==case)) for case in report['groups']}
assert by_case=={'narrow-feasible':{'feasible':5},'narrow-infeasible':{'unresolved':5},'large-finite-snr':{'feasible':5},'fractional-boundary':{'unresolved':5}}
for row in report['records']:
    result=row['additional_tighter_diagnostic']
    if result['status']!='feasible':continue
    power,weak,strong,qw,qs=row['inputs'];assert qw.is_integer() and qs.is_integer()
    A=Fraction.from_float(power)*Fraction.from_float(weak);B=Fraction.from_float(power)*Fraction.from_float(strong)
    a=Fraction.from_float(result['a_star']);tw=2**int(qw)-1;ts=2**int(qs)-1
    residuals=dict(weak_at_weak=(1-a)*A-tw*(1+a*A),weak_at_strong=(1-a)*B-tw*(1+a*B),strong=a*B-ts)
    assert 0<=a<=1 and all(value>=0 for value in residuals.values())
    assert result['feasible']==1.0 and not isinstance(result['feasible'],bool)
    assert result['optimality_status']=='numerical-concavity-bound'
    assert 0<=result['objective_gap_bound']<=report['additional_tighter_policy']['objective_tolerance']
    validated.append(dict(row=row['row'],case_id=row['case_id'],accepted_split_exact_fraction=str(a),exact_original_constraint_residuals={key:str(value) for key,value in residuals.items()},oracle_numerical_gap_bound=result['objective_gap_bound'],oracle_numerical_gap_within_declared_tighter_tolerance=True))
assert len(validated)==10
save(d/'extra-tighter-validation.json',dict(timestamp=now(),status='AUTHOR_EXTRA_TIGHTER_WITNESSES_CHECKED',census_sha256=sha256(d/'census.json'),by_case=by_case,feasible_witnesses_checked=10,exact_original_constraints_checked=True,oracle_gap_claim='Reported numerical bound checked against declared tighter tolerance; no validated interval-arithmetic certification asserted.',witnesses=validated,canonical_results_changed=False,scientific_acceptance=False,independent_results_review=False))
with (d/'census.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write('''\n## Checked results of the extra tighter calls\n\n| Case | Extra tighter results | Original constraints of accepted witnesses |\n|---|---|---|\n| narrow-feasible | 5 feasible | All three original SINR inequalities checked with exact rationals |\n| narrow-infeasible | 5 unresolved | No accepted witness |\n| large-finite-snr | 5 feasible | All three original SINR inequalities checked with exact rationals |\n| fractional-boundary | 5 unresolved | No accepted witness |\n\nAll ten reported numerical objective-gap bounds are within the declared\ntighter objective tolerance. These checks validate the extra diagnostic\nwitnesses, while the twenty canonical base checks retain their actual labels.\nTen extra checks remain unresolved. See extra-tighter-validation.json.\n''')
print(json.dumps(dict(status='CHECKED',extra_feasible=10,extra_unresolved=10,exact_constraint_witnesses=10,canonical_results_changed=False)))
