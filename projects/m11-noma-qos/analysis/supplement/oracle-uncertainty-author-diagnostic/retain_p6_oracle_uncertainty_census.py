import json
import shutil
import subprocess
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.state import provenance

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/oracle-uncertainty-author-diagnostic'
census=load(d/'census.json');validation=load(d/'extra-tighter-validation.json')
assert census['stored_base_unresolved_rows']==20 and census['canonical_tighter_coverage_of_these_rows']==0
assert validation['feasible_witnesses_checked']==10 and validation['census_sha256']==sha256(d/'census.json')
ready=load(p/'analysis/source-review-ready.json')
assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
assert all(sha256(r/name)==digest for name,digest in load(p/'sim/lock.json')['input_hashes'].items())
for name in ['audit_p6_oracle_uncertainty_cases.py','validate_p6_extra_tighter_diagnostic.py','retain_p6_oracle_uncertainty_census.py']:
    shutil.copyfile(r/'.cache'/name,d/name)
save(d/'retention-receipt.json',dict(timestamp=now(),status='AUTHOR_UNCERTAINTY_DIAGNOSTICS_RETAINED',unresolved_base_rows=20,case_groups=4,rows_per_group=5,canonical_tighter_coverage=0,extra_tighter_calls=20,extra_feasible_witnesses_exactly_checked=10,extra_unresolved=10,canonical_counts_unchanged=True,source_and_locked_inputs_unchanged=True,scientific_acceptance=False,evidence={file.name:sha256(file) for file in d.iterdir() if file.is_file()}))
provenance(p,'Retained author census of20unresolved deterministic base-oracle checks across4cases repeated5times: narrow feasible/infeasible, large finite SNR and fractional boundary. None of these rows has canonical tighter coverage. Extra local calls with the already declared10fold tighter policy and unchanged96/256caps resolve10tofeasible and leave10unresolved; exact rational checks validate all10accepted witnesses. Exact domain and objective-gap deductions explain limits. These extra calls remain outside canonical4708/1160coverage; source,51locks, stored labels and scientific gates are unchanged.', ['analysis/supplement/oracle-uncertainty-author-diagnostic/retention-receipt.json','analysis/supplement/oracle-uncertainty-author-diagnostic/census.json','analysis/supplement/oracle-uncertainty-author-diagnostic/extra-tighter-validation.json'],'ai')
with (p/'findings.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write('''\n## P6 remaining oracle uncertainty mapped by case\n\nThe twenty unresolved base-oracle checks belong to four deterministic cases,\neach repeated five times. Canonical tighter checks select rows0-7; none of the\ntwenty unresolved rows is selected. A separate author diagnostic using the\nalready declared tenfold tighter policy and unchanged96/256caps resolves the\nten narrow-feasible/large-SNR rows to feasible, with all original constraints\nchecked using exact rationals. The ten narrow-infeasible/fractional-boundary\nrows remain unresolved. Exact domain and objective-gap deductions explain\nthe numerical limits. These twenty extra calls are outside canonical coverage\nand do not change results, source, protocol, gates or uncertainty acceptance.\nSee analysis/supplement/oracle-uncertainty-author-diagnostic/census.md.\n''')
with (p/'to_human/P6-completed-attempt-status.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write('''\n## Oracle sensitivity coverage and remaining cases\n\nThe twenty unresolved base checks cover four cases repeated five times. None\nwas selected for canonical tighter replay. Extra local diagnostic calls using\nthe existing tighter policy resolve ten narrow-feasible/large-SNR rows, with\nexact checks of their accepted constraints; ten rows remain unresolved.\nCanonical results and replay counts remain unchanged. This informs a future\nreview of certificate handling and sensitivity coverage, after full results.\nSee analysis/supplement/oracle-uncertainty-author-diagnostic/census.md.\n''')
paths=['projects/m11-noma-qos/analysis/supplement/oracle-uncertainty-author-diagnostic','projects/m11-noma-qos/ara/trace/sessions/2026-10-13-0045.yaml','projects/m11-noma-qos/ara/trace/sessions/session_index.yaml','projects/m11-noma-qos/findings.md','projects/m11-noma-qos/to_human/P6-completed-attempt-status.md']
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',*paths],capture_output=True,check=True)
print(json.dumps(dict(status='RETAINED',groups=4,extra_resolved=10,extra_unresolved=10,canonical_counts_unchanged=True)))
