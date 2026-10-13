import json
import shutil
import subprocess
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.state import provenance

r=Path.cwd().resolve();p=r/'projects/m11-noma-qos'
ready=load(p/'analysis/source-review-05/candidate-ready.json')
assert ready['recommendation']=='ready' and ready['enforced_independent_review'] and ready['review_round']==5 and ready['candidate_only']
review_receipt=load(p/ready['receipt'])
assert all(sha256(p/'analysis/source-review-05'/name)==digest for name,digest in review_receipt['evidence'].items())
assert sha256(p/ready['review'])==ready['review_sha256']
prior=load(p/'analysis/source-review-ready.json');assert prior['review_round']==4
for name,digest in prior['source_hashes'].items():
    assert sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest
meta=load(p/'analysis/P6-code-review-round5-payload.json');candidate=r/meta['candidate_repo_relative']
assert ready['candidate_commit']=='aa68d62ac47da40a1a9f2b4890ee780d4ccb1755'
assert ready['source_hashes']==meta['source_hashes']
for name,digest in ready['source_hashes'].items():
    assert sha256(candidate/name.removeprefix('@repo/') if name.startswith('@repo/') else candidate/'projects/m11-noma-qos'/name)==digest
changes=[name for name in prior['source_hashes'] if prior['source_hashes'][name]!=ready['source_hashes'][name]]
assert set(changes)==set(meta['changed_source_paths'])=={'analysis/supplement/independent.py','analysis/supplement/test_supplement.py'}
state=load(p/'research-state.yaml');assert state['phase']=='P6' and all(state['gates'][f'G{i}']['status']=='approved' for i in range(1,6))
lock=load(p/'sim/lock.json')['input_hashes'];assert len(lock)==51
assert all(sha256(r/name)==digest for name,digest in lock.items())
native_marker=load(r/'.cache/p6-canonical-native-active.json')
native_receipt=load(p/native_marker['scientific_receipt'])
assert native_marker['status']=='RECORDED' and native_receipt['status']=='PASS'
assert sha256(p/native_marker['scientific_receipt'])==native_marker['scientific_receipt_sha256']
for name,digest in native_receipt['native_output_hashes'].items():assert sha256(p/name)==digest
d=p/'analysis/supplement/native-output-archive-attempt1'
stage=p/'analysis/verifier-output'
targets=[stage,p/'analysis/verification.json',p/'analysis/verification.yaml',p/'analysis/verification-report.md']
assert not d.exists()
# Resolve and verify every move stays inside the explicitly named project workspace.
for path in [d,*targets]:
    assert path.resolve().is_relative_to(p.resolve()) and path.resolve().is_relative_to(r)
    assert not path.is_symlink()
files=[f for target in targets for f in (target.rglob('*') if target.is_dir() else [target]) if f.is_file()]
assert len(files)==8 and all(not f.is_symlink() for f in files)
original_hashes={f.relative_to(p).as_posix():sha256(f) for f in files}
original_head=subprocess.check_output(['git','-c',f'safe.directory={r.as_posix()}','rev-parse','HEAD'],text=True).strip()
d.mkdir()
shutil.copyfile(p/'analysis/source-review-ready.json',d/'source-review-ready-round4.json')
for target in targets:target.rename(d/target.name)
archive_mapping={name:(d/Path(name).relative_to('analysis')).relative_to(p).as_posix() for name in original_hashes}
assert all(sha256(p/archive_mapping[name])==digest for name,digest in original_hashes.items())
save(d/'archive-receipt.json',dict(timestamp=now(),status='ORIGINAL_NATIVE_OUTPUTS_ARCHIVED_WITHOUT_OVERWRITE',original_git_commit=original_head,native_attempt_receipt=native_marker['scientific_receipt'],native_attempt_receipt_sha256=native_marker['scientific_receipt_sha256'],original_source_hashes=prior['source_hashes'],original_file_hashes=original_hashes,original_to_archive=archive_mapping,original_ready_sha256=sha256(d/'source-review-ready-round4.json'),historical_receipts_unchanged=True,note='Historical receipts retain original paths. Use this exact archive mapping or the recorded Git commit for first-attempt bytes; future active output paths belong to the new attempt.'))
for name in changes:shutil.copyfile(candidate/'projects/m11-noma-qos'/name,p/name)
assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
assert all(sha256(r/name)==digest for name,digest in lock.items())
save(p/'analysis/source-review-ready.json',{**ready,'timestamp':now(),'candidate_only':False,'canonical_source_applied':True,'prior_ready_archive':(d/'source-review-ready-round4.json').relative_to(p).as_posix()})
shutil.copyfile(r/'.cache/apply_p6_reviewed_round5_candidate.py',d/'apply_p6_reviewed_round5_candidate.py')
save(d/'candidate-application-receipt.json',dict(timestamp=now(),status='EXACT_REVIEWED_CANDIDATE_APPLIED',candidate_commit=ready['candidate_commit'],review_round=5,changed_source_paths=changes,source_hashes=ready['source_hashes'],source_ready_sha256=sha256(p/'analysis/source-review-ready.json'),locked_inputs_unchanged=True,locked_inputs_checked=51,scientific_acceptance=False,canonical_rerun_started=False))
provenance(p,'Applied exactly the two analysis source paths from independently reviewed round5 candidate; all19 active source hashes match the ready review and all51 locked inputs are unchanged. Archived all8 first native output files with byte-identical mapping before fresh execution. Original failed supplement, combined assessment and source-ready round4 retained. No scientific gate changed.', ['analysis/source-review-05/receipt.json',(d/'archive-receipt.json').relative_to(p).as_posix(),(d/'candidate-application-receipt.json').relative_to(p).as_posix()],'ai')
print(json.dumps(dict(status='REVIEWED_CANDIDATE_APPLIED',changed_sources=changes,source_bindings=19,locks_unchanged=51,native_files_archived=8,scientific_acceptance=False)))
