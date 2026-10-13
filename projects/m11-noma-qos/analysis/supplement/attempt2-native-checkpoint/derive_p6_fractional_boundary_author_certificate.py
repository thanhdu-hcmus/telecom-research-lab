import csv
import json
from fractions import Fraction
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.simulation import verify_manifest

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/attempt2-native-checkpoint'
d.mkdir(exist_ok=True)
ready=load(p/'analysis/source-review-ready.json');lock=load(p/'sim/lock.json')['input_hashes']
def stable():
    assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
    assert all(sha256(r/name)==digest for name,digest in lock.items())
stable()
cases=load(p/'sim/cases.yaml')['cases'];case=cases[16]
assert case==dict(id='fractional-boundary',values=[1,1,1,0.5,0.5])
manifests=[f for f in (p/'results/runs').glob('*/manifest.json') if load(f)['params']['kind']=='deterministic']
assert len(manifests)==1
file=manifests[0];raw_manifest=load(file);verify_manifest(p,raw_manifest)
outputs={Path(value['path']).name:value for value in raw_manifest['outputs']}
channel=p/outputs['channels.csv']['path'];metric=p/outputs['metrics.csv']['path']
assert sha256(channel)==outputs['channels.csv']['sha256'] and sha256(metric)==outputs['metrics.csv']['sha256']
with channel.open(encoding='utf-8',newline='') as cf,metric.open(encoding='utf-8',newline='') as mf:
    channels=list(csv.DictReader(cf));metrics=list(csv.DictReader(mf))
assert len(channels)==len(metrics)==100
rows=[]
for index in [16,36,56,76,96]:
    raw=channels[index];met=metrics[index]
    assert raw['case_id']=='fractional-boundary'
    assert [float(raw[key]) for key in ['P','gw','gs','qw','qs']]==[1,1,1,0.5,0.5]
    assert raw['status']==raw['oma_status']=='unresolved' and raw['certificate']=='none'
    assert raw['a_star']==raw['candidate_a']=='nan' and met['feasible']==met['oma_feasible']=='nan'
    lower=Fraction.from_float(float(raw['interval_lower']));upper=Fraction.from_float(float(raw['interval_upper']))
    lower_residual=(1+lower)**2-2;upper_residual=(1+upper)**2-2
    assert 0<=lower<upper<=1 and lower_residual<0<upper_residual
    rows.append(dict(row=index,stored_noma_status=raw['status'],stored_oma_status=raw['oma_status'],stored_certificate=raw['certificate'],stored_optimizer=raw['a_star'],lower_exact_fraction=str(lower),upper_exact_fraction=str(upper),root_polynomial_lower_residual=str(lower_residual),root_polynomial_upper_residual=str(upper_residual),bracket_width_exact=str(upper-lower),positive_root_strictly_inside_recorded_bracket=True))
stable()
report=dict(timestamp=now(),status='AUTHOR_DEDUCTIVE_CERTIFICATE_ONLY',case_id=case['id'],inputs=case['values'],scope='Exactly five repeats of the approved deterministic case; no Monte Carlo extrapolation.',noma_real_model_feasible=True,noma_exact_optimizer='sqrt(2)-1',noma_feasible_set='singleton {sqrt(2)-1}',noma_exact_rates=dict(weak='1/2',weak_at_strong='1/2',strong='1/2',sum='1'),oma_real_model_feasible=True,oma_exact_rates=dict(weak='1/2',strong='1/2',sum='1'),polynomial='a^2+2*a-1=0, unique root in [0,1]',binary64_split_can_satisfy_both_exact_real_targets=False,stored_rows=rows,stored_labels_changed=False,independent_results_review=False,accepted_manuscript_claim=False,scientific_gate_approval=False,source_and_locked_inputs_unchanged=True,evidence=dict(model='model/model-spec.tex',model_sha256=sha256(p/'model/model-spec.tex'),cases='sim/cases.yaml',cases_sha256=sha256(p/'sim/cases.yaml'),manifest=file.relative_to(p).as_posix(),manifest_sha256=sha256(file),channels=channel.relative_to(p).as_posix(),channels_sha256=sha256(channel),metrics=metric.relative_to(p).as_posix(),metrics_sha256=sha256(metric)),limits=['Exact symbolic deduction by the author, not an independently accepted runtime certificate.','Stored NOMA/OMA unresolved labels and the combined assessment remain authoritative for the current frozen execution.','No simulation, approved source, model, protocol, tolerance, gate or deviation is changed.','A future machine-readable algebraic-certificate extension requires a separate reviewed implementation and any necessary PI decisions.'])
save(d/'fractional-boundary-author-certificate.json',report)
(d/'fractional-boundary-author-certificate.md').write_text('''# Author certificate for the fractional boundary

Status: author deduction; independent numerical-results review remains pending.
The active verifier and all saved unresolved labels remain unchanged.

## Exact approved case

The deterministic case has P = 1, g_w = g_s = 1 and q_w = q_s = 1/2.
It appears at rows 16, 36, 56, 76 and 96 of the manifest bound in the JSON receipt.

## NOMA derivation

Both weak-message decoding sites have the same capacity. The approved model
reduces to R_w(a) = log2(2/(1+a)) and R_s(a) = log2(1+a).
The weak target requires 1+a <= sqrt(2), and the strong target requires
1+a >= sqrt(2). Thus the exact real feasible set is the singleton
a = sqrt(2)-1. Both weak decoding sites and the strong rate are exactly 1/2;
the total is 1 bit/s/Hz. This is a single approved-case deduction.

The polynomial f(a) = (1+a)^2-2 is strictly increasing on [0,1]. Exact Fraction
arithmetic confirms f(recorded lower bracket) < 0 < f(recorded upper bracket)
for each of the five actual saved rows. The root lies inside those brackets.

Every finite binary64 number is rational, while sqrt(2)-1 is irrational. Hence
no binary64 split satisfies both exact real inequalities simultaneously. The
saved rows contain no accepted optimizer or exact-split certificate. A rounded
split and a real-model algebraic witness have different representational roles.

## OMA derivation

Each matched full-power slot has capacity log2(2)=1. The whole-block factor
1/2 gives each user's rate exactly 1/2, with total 1 bit/s/Hz. Both exact real
targets are met at equality. The recorded OMA rates agree numerically, while
the current conservative boundary classifier leaves their labels unresolved.

## Consequence for the current run

This explains the known fractional-boundary uncertainty. It does not amend
the frozen verifier, upgrade stored statuses, replace the pending independent
results review or approve a scientific gate. The full corrected run and its
combined assessment must retain their actual uncertainty. A proposed algebraic
certificate implementation belongs in a separately reviewed change, with any
required PI decisions before changes to locked source or protocol.
''',encoding='utf-8',newline='\n')
print(json.dumps(dict(status=report['status'],saved_rows=len(rows),brackets_checked_with_exact_rationals=True,stored_labels_changed=False)))
