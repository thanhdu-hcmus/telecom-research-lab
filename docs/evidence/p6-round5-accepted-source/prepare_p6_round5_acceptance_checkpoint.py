import shutil
import subprocess
from pathlib import Path
from lab.io import load,save,sha256,now

r=Path.cwd();p=r/'projects/m11-noma-qos';d=r/'docs/evidence/p6-round5-accepted-source'
d.mkdir(exist_ok=False)
for name in ['record_p6_round5_explicit_authorization.py','record_p6_round5_running_status.py','save_p6_review_round5.py','apply_p6_reviewed_round5_candidate.py','prepare_p6_attempt2_helpers.py','run_p6_canonical_attempt2_step.py','finish_p6_canonical_attempt2_assessment.py','prepare_p6_round5_acceptance_checkpoint.py']:
    shutil.copyfile(r/'.cache'/name,d/name)
ready=load(p/'analysis/source-review-ready.json');assert ready['review_round']==5 and ready['canonical_source_applied']
assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
with (p/'findings.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write('\n## P6 fifth enforced source review READY; correction applied\n\nThe fifth review returned READY with zero findings. The actual root and fresh\nresults verifier were read-only with approval never; the reviewer made no tool\ncalls, and all source and review-workspace bytes remained unchanged. OpenAI\nprovider metadata and sanitized fresh-fork evidence are retained in\nanalysis/source-review-05. The exact two reviewed analysis source paths are now\napplied, with all 19 active source hashes matching the review and all 51 locked\ninputs unchanged. All 133 supplemental unit cases and changed-source lint and\nformat checks pass. The framework suite is running.\n\nAll eight original native output files were archived byte-identically with an\nexplicit path mapping under analysis/supplement/native-output-archive-attempt1.\nThe original combined FAIL and uncertainty remain historical evidence. Fresh\ncanonical execution has not yet launched; scientific acceptance and G6/G7\nremain pending. The earlier transfer rejection and source-review-running\nsections are historical.\n')
status=p/'to_human/P6-completed-attempt-status.md'
text=status.read_text(encoding='utf-8')
start=text.index('The PI explicitly authorized the exact private packet transfer.')
end=text.index('\n\n## Uncertainty',start)
text=text[:start]+'''The explicitly authorized fifth source review returned READY with zero findings.
Actual read-only root/child policies, no reviewer tools, fresh fork, OpenAI
provider and unchanged bytes were audited. The exact two reviewed analysis
source paths are applied; all 19 source bindings and 51 locked inputs match.
The original eight native output files are archived with byte-identical mapping
for the fresh rerun. All 133 supplemental unit cases pass; the framework suite
is running. Canonical corrected execution has not started yet.''' +text[end:]
status.write_text(text,encoding='utf-8',newline='\n')
audit=r/'docs/remaining-work-audit.md';text=audit.read_text(encoding='utf-8')
text=text.replace('The automatic approval review rejected the fifth external review\nlaunch pending explicit private-packet/destination authorization. No review\nwas launched or transmitted.', 'The PI explicitly authorized the exact fifth private source packet transfer.\nThe fifth enforced independent source review returned READY with zero findings;\nits effective read-only/no-tool/fresh-fork/provider and byte-integrity audits are\nretained. The exact two reviewed analysis source paths are now applied, all19\nactive source bindings match, and all51 locked inputs are unchanged. Original\nnative outputs are archived byte-identically for a fresh canonical rerun.')
text=text.replace('P6 still needs independent candidate source review, the corrected canonical', 'P6 still needs the corrected canonical')
audit.write_text(text,encoding='utf-8',newline='\n')
unit=load(p/'analysis/supplement/unit-test-results.json');assert unit['status']=='PASS' and unit['tests_run']==133
save(d/'local-checks.json',dict(timestamp=now(),supplemental_unit_tests=133,unit_status='PASS',unit_failures=unit['failures'],unit_errors=unit['errors'],unit_source_hashes_unchanged=unit['source_hashes_unchanged'],unit_receipt_sha256=sha256(p/'analysis/supplement/unit-test-results.json'),changed_source_lint='PASS',changed_source_format_check='PASS',framework_suite='RUNNING',scientific_acceptance=False,canonical_rerun_started=False))
g=['git','-c',f'safe.directory={r.as_posix()}']
paths=['docs/remaining-work-audit.md',d.relative_to(r).as_posix(),'projects/m11-noma-qos/findings.md','projects/m11-noma-qos/to_human/P6-completed-attempt-status.md','projects/m11-noma-qos/ara/trace/sessions/session_index.yaml','projects/m11-noma-qos/ara/trace/sessions/2026-10-13-0040.yaml','projects/m11-noma-qos/ara/trace/sessions/2026-10-13-0041.yaml','projects/m11-noma-qos/ara/trace/sessions/2026-10-13-0042.yaml','projects/m11-noma-qos/analysis/P6-code-review-round5-explicit-authorization.json','projects/m11-noma-qos/analysis/P6-code-review-round5-launch.json','projects/m11-noma-qos/analysis/source-review-05','projects/m11-noma-qos/analysis/source-review-ready.json','projects/m11-noma-qos/analysis/supplement/independent.py','projects/m11-noma-qos/analysis/supplement/test_supplement.py','projects/m11-noma-qos/analysis/supplement/unit-test-results.json','projects/m11-noma-qos/analysis/supplement/unit-runs/f9c0170db75d458197f1e45bf28ca6cb','projects/m11-noma-qos/analysis/supplement/native-output-archive-attempt1','projects/m11-noma-qos/analysis/verifier-output','projects/m11-noma-qos/analysis/verification.json','projects/m11-noma-qos/analysis/verification.yaml','projects/m11-noma-qos/analysis/verification-report.md']
cr=[file.relative_to(r).as_posix() for base in [d,p/'analysis/source-review-05',p/'analysis/supplement/native-output-archive-attempt1'] for file in base.rglob('*') if file.is_file() and b'\r\n' in file.read_bytes()]
if cr:
    with (r/'.gitattributes').open('a',encoding='utf-8',newline='\n') as out:out.write('\n# Preserve exact accepted P6 round5 review and historical archive bytes.\n'+''.join(name+' -text whitespace=cr-at-eol,-blank-at-eof\n' for name in cr))
    paths.append('.gitattributes')
subprocess.run(g+['add','--',*paths],capture_output=True,check=True)
print(f'Staged source-readiness checkpoint and preserved {len(cr)} CRLF evidence files.')
