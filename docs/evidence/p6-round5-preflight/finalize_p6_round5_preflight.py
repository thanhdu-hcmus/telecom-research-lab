import shutil
import subprocess
from pathlib import Path
from lab.io import load, save, sha256, now

r=Path.cwd()
p=r/'projects/m11-noma-qos'
d=r/'docs/evidence/p6-round5-preflight'
native=load(r/'.cache/p6-round5-preflight-native-secrets.json')
assert native['status']=='PASS' and native['files_scanned']==2604 and not native['findings']
index=load(r/'.cache/p6-round5-preflight-index-bindings.json')
assert index['status']=='PASS' and index['locked_inputs_checked']==51 and index['approved_index_bindings']==1002 and not index['mismatches']
assert not (p/'analysis/P6-code-review-round5-launch.json').exists()
blocked=load(p/'analysis/P6-code-review-round5-transfer-blocked.json')
assert not blocked['transmitted'] and not blocked['reviewer_launched']
diagnostic=load(p/'analysis/supplement/candidate-round5-author-diagnostic/retention-receipt.json')
assert diagnostic['row_errors']==0 and diagnostic['rows']==4718692 and diagnostic['jobs']==145
for name in ['native-secrets','index-bindings']:
    shutil.copyfile(r/f'.cache/p6-round5-preflight-{name}.json',d/f'{name}.json')
shutil.copyfile(r/'.cache/finalize_p6_round5_preflight.py',d/'finalize_p6_round5_preflight.py')
save(d/'checkpoint-receipt.json',dict(timestamp=now(),status='LOCAL_CHECKPOINT_READY',author_diagnostic_jobs=145,author_diagnostic_rows=4718692,author_row_errors=0,scientific_acceptance=False,canonical_corrected_rerun_started=False,external_source_review_launched=False,external_source_packet_transmitted=False,automatic_transfer_review='REJECTED; explicit private packet and destination authorization requested',native_secrets=native,index_bindings=index,candidate_diagnostic_retention_sha256=sha256(p/'analysis/supplement/candidate-round5-author-diagnostic/retention-receipt.json'),transfer_blocked_sha256=sha256(p/'analysis/P6-code-review-round5-transfer-blocked.json'),evidence={f.name:sha256(f) for f in d.iterdir() if f.is_file()}))
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',d.relative_to(r).as_posix()],check=True,capture_output=True)
print('Local checkpoint ready; no external review launched or transmitted.')
