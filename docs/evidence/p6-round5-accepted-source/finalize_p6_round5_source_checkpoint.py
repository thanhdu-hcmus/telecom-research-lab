import shutil
import subprocess
from pathlib import Path
from lab.io import load,save,sha256,now

r=Path.cwd();p=r/'projects/m11-noma-qos';d=r/'docs/evidence/p6-round5-accepted-source'
native=load(r/'.cache/p6-round5-accepted-source-native-secrets.json')
assert native['status']=='PASS' and native['files_scanned']==2626 and not native['findings']
audit=load(r/'.cache/p6-round5-accepted-source-secret-audit.json')
assert audit['status']=='PASS' and not audit['unreviewed']
ready=load(p/'analysis/source-review-ready.json');assert ready['review_round']==5 and ready['canonical_source_applied']
assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
lock=load(p/'sim/lock.json')['input_hashes'];assert len(lock)==51 and all(sha256(r/name)==digest for name,digest in lock.items())
for name in ['framework-test-receipt.json','local-checks.json']:
    value=load(d/name)
    if name.startswith('framework'):assert value['status']=='PASS' and value['tests']==97
    else:assert value['unit_status']=='PASS' and value['supplemental_unit_tests']==133 and value['framework_suite']=='PASS'
shutil.copyfile(r/'.cache/p6-round5-accepted-source-native-secrets.json',d/'native-secrets.json')
shutil.copyfile(r/'.cache/p6-round5-accepted-source-index-bindings.json',d/'index-bindings.json')
shutil.copyfile(r/'.cache/finalize_p6_round5_source_checkpoint.py',d/'finalize_p6_round5_source_checkpoint.py')
shutil.copyfile(r/'.cache/prepare_p6_round5_acceptance_audits.py',d/'prepare_p6_round5_acceptance_audits.py')
save(d/'checkpoint-receipt.json',dict(timestamp=now(),status='ENFORCED_SOURCE_READY_LOCAL_CHECKS_PASS',source_review_round=5,source_review_sha256=sha256(p/'analysis/source-review-05/receipt.json'),source_ready_sha256=sha256(p/'analysis/source-review-ready.json'),source_hashes=ready['source_hashes'],framework_tests=97,supplemental_unit_tests=133,native_secret_scan=native,locked_inputs_checked=51,locked_inputs_unchanged=True,canonical_corrected_execution_started=False,scientific_acceptance=False,external_numerical_results_review_authorized=False,evidence={file.name:sha256(file) for file in d.iterdir() if file.is_file()}))
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',d.relative_to(r).as_posix()],capture_output=True,check=True)
print('Source-readiness checkpoint ready; canonical corrected execution still pending.')
