import json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
from lab.io import sha256
repo=Path.cwd()
area=repo/'projects/m11-noma-qos/analysis/source-review-01/physics-repair/run-1791784691000'
supp=repo/'projects/m11-noma-qos/analysis/supplement'
def observed(name):
    text=(area/name).read_text(encoding='utf-8')
    count=re.search(r'Ran (\d+) tests? in ([\d.]+)s',text)
    failed=re.search(r'FAILED \(([^)]*)\)',text)
    return {'tests':int(count[1]),'elapsed_s':float(count[2]),'verdict':'FAIL' if failed else 'PASS','failure_summary':failed[1] if failed else None}
sources={name:sha256(supp/name) for name in ('independent.py','test_supplement.py')}
files=['red-01.log','red-01.json','green-01.log','green-01.json','full-suite-01.log','full-suite-01.json','lint-final.log','format-final.log','lint-final.json']
lint=json.loads((area/'lint-final.json').read_text(encoding='utf-8'))
result={'status':'PHYSICS_REPAIRS_PREPARED; INTEGRATION_ERRORS_RETAINED',
'findings_addressed':['F04','F06','F07','F11'],
'public_api_compatible':True,'canonical_execution':False,'external_transmission':False,
'red':observed('red-01.log'),'assigned_regressions':observed('green-01.log'),
'full_isolated_suite':observed('full-suite-01.log'),'lint':lint,
'source_hashes':sources,'evidence_hashes':{name:sha256(area/name) for name in files},
'non_physics_errors':['ReplayTests.test_replay_bad_input_coverage_caps_and_certificates','ReplayTests.test_replay_clean_and_missing_tighter','ReplayTests.test_replay_compensating_rates_and_mask','ReplayTests.test_tighter_comparison_uses_tighter_policy','StructuralTests.test_disposable_csv_empty_missing_duplicate_and_schema'],
'non_physics_cause':"Concurrent parent replay.py expects optimality_status absent from existing synthetic solver fixture; no parent source or original fixture semantics changed.",
'changes':{'F04':'Discrete index with SPLIT representation check, recorded-split original constraints and objective recomputation.',
'F06':'Selected upper endpoint and weak target activation checks; original decoding-site constraints and per-row ablation loss >= -OBJECTIVE.',
'F07':'Uncertified noninteger inner separation <= SPLIT retains unresolved status.',
'F11':'Positive received-product underflow excluded; classifiers unresolved, rates fail closed. Structural equality uses exact common-power algebra P=0 or gw=gs.'},
'limits':['Numerical endpoint/activation/grid checks use the existing declared tolerances; they are not universal floating-point proofs.',
'Noninteger narrow brackets remain unresolved without a certificate.',
'Underflow is an unsupported numeric domain, not exact zero capacity.',
'Full canonical execution and scientific gate decisions remain excluded.',
'Full isolated suite is not green until parent integrates the concurrent replay fixture requirements.']}
target=area/'physics-evidence.json'
if target.exists():raise RuntimeError('Evidence overwrite refused')
target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert all(sha256(supp/name)==h for name,h in sources.items())
print(json.dumps({'assigned_regressions':result['assigned_regressions'],'full_isolated_suite':result['full_isolated_suite'],'lint':lint,'source_hashes':sources,'evidence_sha256':sha256(target)},indent=2))
