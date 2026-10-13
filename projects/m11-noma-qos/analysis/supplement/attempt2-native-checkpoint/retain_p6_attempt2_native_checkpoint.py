import json
import shutil
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.state import provenance
from lab.models import VerificationItem

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/attempt2-native-checkpoint'
marker=load(r/'.cache/p6-canonical-attempt2-native-active.json')
assert marker['status']=='RECORDED' and marker['scientific_status']=='PASS' and marker['exit_code']==0
file=p/marker['scientific_receipt'];assert sha256(file)==marker['scientific_receipt_sha256']
native=load(file)
assert native['status']=='PASS' and native['native_api_invoked'] and native['canonical_scientific_subprocess_executed'] and native['reviewed_source_bindings_rechecked'] and not native['stage_existed_before']
ready=load(p/'analysis/source-review-ready.json');assert native['reviewed_source_hashes']==ready['source_hashes']
assert all(sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest for name,digest in ready['source_hashes'].items())
assert all(sha256(r/name)==digest for name,digest in load(p/'sim/lock.json')['input_hashes'].items())
assert all(sha256(p/name)==digest for name,digest in native['native_output_hashes'].items())
assert all(value['passed'] for value in native['native_report']['checks'].values())
items=[VerificationItem.model_validate(value) for value in load(p/'analysis/verification.yaml')]
assert len(items)==7 and all(item.verdict=='PASS' for item in items)
completion=load(file.parent/'completion-receipt.json')
assert all(sha256(p/name)==digest for name,digest in completion['evidence_hashes'].items())
target=d/'native-control';target.mkdir(exist_ok=False)
for source in (r/marker['directory']).iterdir():
    if source.is_file():shutil.copyfile(source,target/source.name)
save(target/'final-operation-marker.json',marker)
for name in ['derive_p6_fractional_boundary_author_certificate.py','compute_p6_attempt2_provisional_native_claims.py','retain_p6_attempt2_native_checkpoint.py']:
    shutil.copyfile(r/'.cache'/name,d/name)
supp=load(r/'.cache/p6-canonical-attempt2-supplement-active.json');assessment=load(r/'.cache/p6-canonical-attempt2-assessment-active.json')
records=[]
for line in (r/supp['directory']/'stdout.txt').read_text(encoding='utf-8').splitlines():
    try:value=json.loads(line)
    except json.JSONDecodeError:continue
    if 'run_id' in value and 'rows' in value:records.append(value)
snapshot=dict(timestamp=now(),status='PARTIAL_SUPPLEMENT_PROGRESS',jobs=len(records),rows=sum(value['rows'] for value in records),row_errors=sum(value['row_error_count'] for value in records),ambiguity_entries=sum(value['ambiguity_entries'] for value in records),base_replays=sum(value['replay']['base'] for value in records),tighter_replays=sum(value['replay']['tighter'] for value in records),jobs_detail=records,scientific_acceptance=False)
save(d/'supplement-progress-snapshot.json',snapshot)
claims=load(d/'provisional-native-claims.json');assert claims['native_arithmetic_checks']==9 and not claims['scientific_acceptance']
certificate=load(d/'fractional-boundary-author-certificate.json');assert len(certificate['stored_rows'])==5 and not certificate['stored_labels_changed']
save(d/'checkpoint-receipt.json',dict(timestamp=now(),status='FRESH_NATIVE_PASS_SUPPLEMENT_IN_PROGRESS',native_receipt=marker['scientific_receipt'],native_receipt_sha256=marker['scientific_receipt_sha256'],native_status='PASS',native_runtime_s=marker['runtime_s'],native_checks=8,native_prediction_items=7,source_review_round=5,source_bindings_unchanged=True,locked_inputs_unchanged=True,supplement_status=supp['status'],assessment_status=assessment['status'],completed_supplement_jobs=snapshot['jobs'],completed_supplement_rows=snapshot['rows'],row_errors=snapshot['row_errors'],provisional_arithmetic_checks=9,fractional_boundary_author_certificate_rows=5,scientific_acceptance=False,external_numerical_results_review_authorized=False,evidence={source.relative_to(p).as_posix():sha256(source) for source in d.rglob('*') if source.is_file()}))
provenance(p,'Fresh attempt2 native verifier completed PASS with ordinary unmodified API, fresh output stage, all8checks and7prediction items passing, exact reviewed19-source bindings and51locks unchanged. Supplemental execution and combined assessment remain pending. Retained actual partial progress, revalidated9provisional arithmetic values through unmodified evaluate_claim, and derived an author-only exact sqrt(2)-1 certificate for five repeated fractional-boundary rows. Existing unresolved labels, source/model/protocol, gates and deviations remain unchanged; no scientific full PASS or accepted manuscript claim.', ['analysis/supplement/attempt2-native-checkpoint/checkpoint-receipt.json','analysis/supplement/attempt2-native-checkpoint/fractional-boundary-author-certificate.json','analysis/supplement/attempt2-native-checkpoint/provisional-native-claims.json'],'ai')
with (p/'findings.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write(f'\n## P6 attempt two native PASS; full supplement pending\n\nThe fresh native verifier completed PASS on 2026-10-13 at 08:27 UTC using the\nunmodified production API and a fresh stage. All eight checks and seven\nprediction items pass; all reviewed source and locked-input bindings match.\nThe partial supplement snapshot at {snapshot["timestamp"]} covers\n{snapshot["jobs"]}/145 jobs and {snapshot["rows"]:,} rows with {snapshot["row_errors"]} row errors.\nFull supplemental completion and combined assessment remain pending.\n\nNine actual per-seed zero-QoS arithmetic values were revalidated and match the\noriginal provisional values exactly; no manuscript claim was registered. An\nauthor-only exact symbolic certificate establishes the singleton sqrt(2)-1\nand matched OMA equality for the five fractional-boundary repeats. Exact\nrational checks validate their recorded brackets. This separate certificate\nhas not received independent results review and does not upgrade stored\nclassifications or the frozen runtime assessment. G6/G7 remain invalidated.\nSee analysis/supplement/attempt2-native-checkpoint for exact receipts and limits.\n')
status=p/'to_human/P6-completed-attempt-status.md';text=status.read_text(encoding='utf-8')
text+='''\n## Latest corrected-attempt native result\n\nFresh native verification completed PASS on 2026-10-13 at 08:27 UTC. All eight\nchecks and seven prediction items pass, with source and locked-input bindings\nunchanged. The full supplement is running; combined assessment is pending.\nNine provisional arithmetic examples have been revalidated unchanged.\n\nAn author-only certificate derives the exact fractional-boundary NOMA split\nsqrt(2)-1 and OMA equality for the five repeated saved rows, including exact\nrational bracket checks. It explains the boundary representation issue;\nexisting unresolved labels and the frozen verifier remain unchanged.\nIndependent numerical-results review and actual PI scientific decisions remain\nrequired. See analysis/supplement/attempt2-native-checkpoint.\n'''
status.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps(dict(status='NATIVE_CHECKPOINT_RETAINED',native='PASS',supplement_jobs=snapshot['jobs'],supplement_rows=snapshot['rows'],row_errors=snapshot['row_errors'],scientific_acceptance=False)))
