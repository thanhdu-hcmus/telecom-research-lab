import json
import shutil
import subprocess
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.state import provenance

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/attempt2-launch'
d.mkdir(exist_ok=False)
markers={kind:load(r/f'.cache/p6-canonical-attempt2-{kind}-active.json') for kind in ['native','supplement','assessment']}
assert markers['native']['status']=='RUNNING' and markers['supplement']['status']=='RUNNING' and markers['assessment']['status']=='WAITING'
ready=load(p/'analysis/source-review-ready.json');assert ready['review_round']==5
assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
assert all(sha256(r/name)==digest for name,digest in load(p/'sim/lock.json')['input_hashes'].items())
for kind,record in markers.items():
    save(d/f'{kind}-initial-marker.json',record)
    shutil.copyfile(r/record['directory']/'launch.json' if kind!='assessment' else r/f'.cache/p6-canonical-attempt2-{kind}-active.json',d/f'{kind}-launch-record.json')
jobs=[]
for line in (r/markers['supplement']['directory']/'stdout.txt').read_text(encoding='utf-8').splitlines():
    try:value=json.loads(line)
    except json.JSONDecodeError:continue
    if 'run_id' in value and 'rows' in value:jobs.append(value)
save(d/'initial-progress-snapshot.json',dict(timestamp=now(),status='IN_PROGRESS',completed_jobs=len(jobs),completed_rows=sum(j['rows'] for j in jobs),row_errors=sum(j['row_error_count'] for j in jobs),jobs=jobs,scientific_acceptance=False,limits='Partial execution snapshot; not final canonical verification.'))
head=subprocess.check_output(['git','-c',f'safe.directory={r.as_posix()}','rev-parse','HEAD'],text=True).strip()
assert head=='fd2877faa2629e6a7cb98b82b661ed1a89108ef0'
save(d/'launch-receipt.json',dict(timestamp=now(),status='FRESH_CORRECTED_CANONICAL_OPERATIONS_RUNNING',attempt=2,source_review_round=5,source_commit=head,source_ready_sha256=sha256(p/'analysis/source-review-ready.json'),planned_jobs=145,planned_rows=4718692,planned_base_replays=4708,planned_tighter_replays=1160,source_bindings_unchanged=True,locked_inputs_unchanged=True,combined_assessment_watcher='WAITING_FOR_BOTH_COMPLETE_RECEIPTS',scientific_acceptance=False,external_numerical_results_review_authorized=False,evidence={file.name:sha256(file) for file in d.iterdir() if file.is_file()}))
shutil.copyfile(r/'.cache/record_p6_attempt2_launch_checkpoint.py',d/'record_p6_attempt2_launch_checkpoint.py')
provenance(p,'Fresh corrected P6 native and supplemental canonical operations launched from reviewed committed source fd2877f in separate unique attempt2 directories. Supplement covers145jobs/4718692rows with4708base/1160tighterreplays under ordinary guards; automatic combined assessor waits for both matching completed receipts. All19sourcebindings and51locks unchanged. First partial progress snapshot retained; no completion or scientific PASS asserted. G6/G7 remain invalidated; numerical-results review excluded.', ['analysis/supplement/attempt2-launch/launch-receipt.json','analysis/supplement/attempt2-launch/initial-progress-snapshot.json'],'ai')
with (p/'findings.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write('\n## P6 corrected canonical attempt two running\n\nFresh native and supplemental operations launched on 2026-10-13 at 07:52 UTC\nfrom committed reviewed source fd2877f, with an automatic combined-assessment\nwatcher. Planned full coverage remains 145 jobs / 4,718,692 rows, 4,708 base and\n1,160 tighter shared-oracle replays. Every active source binding and all 51\nlocked inputs match. Initial partial progress is retained in\nanalysis/supplement/attempt2-launch; it is not completion or scientific PASS.\nOriginal first-attempt evidence and explicit unresolved scope remain retained.\nG6/G7 remain invalidated; no external numerical-results review is authorized.\n')
status=p/'to_human/P6-completed-attempt-status.md';text=status.read_text(encoding='utf-8')
text=text.replace('Canonical corrected execution has not started yet.', 'Fresh native and supplemental canonical execution launched on 2026-10-13\nat 07:52 UTC from fd2877f. The automatic watcher will run combined assessment\nafter both matching receipts finish. Coverage remains 145 jobs / 4,718,692\nrows. Progress is partial; scientific acceptance is pending.')
status.write_text(text,encoding='utf-8',newline='\n')
audit=r/'docs/remaining-work-audit.md';text=audit.read_text(encoding='utf-8')
text=text.replace('P6 still needs the corrected canonical\nrerun and combined assessment, executable accepted manuscript claims, and', 'The fresh corrected native and supplemental canonical runs are active, with\nan automatic combined-assessment watcher. Their completion remains pending.\nP6 still needs completed corrected verification and combined assessment,\nexecutable accepted manuscript claims, and')
audit.write_text(text,encoding='utf-8',newline='\n')
paths=['projects/m11-noma-qos/analysis/supplement/attempt2-launch','projects/m11-noma-qos/ara/trace/sessions/2026-10-13-0043.yaml','projects/m11-noma-qos/ara/trace/sessions/session_index.yaml','projects/m11-noma-qos/findings.md','projects/m11-noma-qos/to_human/P6-completed-attempt-status.md','docs/remaining-work-audit.md']
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',*paths],capture_output=True,check=True)
print(json.dumps(dict(status='LAUNCH_AND_PROGRESS_RETAINED',completed_jobs=len(jobs),completed_rows=sum(j['rows'] for j in jobs),row_errors=sum(j['row_error_count'] for j in jobs))))
