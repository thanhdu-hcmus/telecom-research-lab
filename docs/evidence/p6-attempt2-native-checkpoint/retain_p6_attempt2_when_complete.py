"""Retain completed local verification evidence; no gates or external calls."""
import json
import shutil
import sys
import time
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.state import provenance

r=Path.cwd();p=r/'projects/m11-noma-qos'
marker=r/'.cache/p6-attempt2-completion-retention-active.json'
assert not marker.exists(),'Completion retention already launched; inspect existing marker'
record=dict(status='WAITING',started=now(),scientific_acceptance=False,external_review_launched=False)
save(marker,record);print(json.dumps(record),flush=True)
started=time.monotonic()
try:
    while True:
        steps={kind:load(r/f'.cache/p6-canonical-attempt2-{kind}-active.json') for kind in ['native','supplement','assessment']}
        if steps['assessment']['status'] not in ['WAITING','ASSESSING']:break
        if time.monotonic()-started>92000:raise TimeoutError('Completion retention deadline exceeded')
        time.sleep(30)
    d=p/'analysis/supplement/completed-attempt-02';d.mkdir(exist_ok=False)
    for kind,operation in steps.items():
        target=d/'control'/kind;target.mkdir(parents=True)
        for file in (r/operation['directory']).iterdir():
            if file.is_file():shutil.copyfile(file,target/file.name)
        save(target/'final-operation-marker.json',operation)
    shutil.copyfile(r/'.cache/retain_p6_attempt2_when_complete.py',d/'retain_p6_attempt2_when_complete.py')
    if not all(operation['status']=='RECORDED' for operation in steps.values()):
        summary=dict(status='INCOMPLETE_OPERATION_RETAINED',operations=steps,scientific_acceptance=False,external_numerical_results_review_authorized=False)
    else:
        reports={}
        for kind,operation in steps.items():
            relative=operation.get('scientific_receipt',operation.get('assessment'))
            digest=operation.get('scientific_receipt_sha256',operation.get('assessment_sha256'))
            file=p/relative;assert sha256(file)==digest
            reports[kind]=load(file)
            completion=load(file.parent/'completion-receipt.json')
            assert all(sha256(p/name)==expected for name,expected in completion['evidence_hashes'].items())
        supp=reports['supplement'];assessment=reports['assessment'];native=reports['native']
        summary=dict(status='COMPLETED_CANONICAL_ATTEMPT_RETAINED',native_status=native['status'],supplement_status=supp['status'],combined_status=assessment['status'],jobs=len(supp.get('jobs',[])),rows=sum(job['rows'] for job in supp.get('jobs',[])),error_counts=supp.get('error_counts',{}),source_bindings_rechecked=supp.get('source_bindings_rechecked'),inventory_paths_rechecked=supp.get('inventory_paths_rechecked'),input_bindings_rechecked=supp.get('bindings_rechecked'),eligible_for_gate_request=assessment.get('eligible_for_gate_request',False),failed_precision=assessment.get('failed_precision',[]),scientific_acceptance=False,external_numerical_results_review_authorized=False,scientific_receipts={kind:operation.get('scientific_receipt',operation.get('assessment')) for kind,operation in steps.items()},note='Actual runtime results retained. Scientific gates remain PI-only; any independent numerical-results transmission needs separate authorization. The author boundary certificate has not upgraded stored labels.')
    summary.update(timestamp=now(),evidence={file.relative_to(p).as_posix():sha256(file) for file in d.rglob('*') if file.is_file()})
    save(d/'closure-receipt.json',summary)
    provenance(p,'Automatically retained the completed second canonical operation receipts and control logs with exact evidence hashes. Actual native/supplement/combined statuses are recorded in closure-receipt.json; no full scientific acceptance, numerical-results transmission or scientific gate decision is made. Original attempt and author certificate remain separate.', ['analysis/supplement/completed-attempt-02/closure-receipt.json'],'ai')
    line='Second canonical attempt completion: '+json.dumps({key:value for key,value in summary.items() if key not in ['evidence','scientific_receipts','operations']},ensure_ascii=False)
    with (p/'findings.md').open('a',encoding='utf-8',newline='\n') as out:out.write('\n## P6 second attempt completion retained automatically\n\n'+line+'\n\nSee analysis/supplement/completed-attempt-02/closure-receipt.json. Scientific\nacceptance, independent results review and PI gates remain pending.\n')
    with (p/'to_human/P6-completed-attempt-status.md').open('a',encoding='utf-8',newline='\n') as out:out.write('\n## Second-attempt completion\n\n'+line+'\n\nThe closure receipt retains actual results and failure/uncertainty scope.\nNo scientific gate or external numerical-results review was performed.\n')
    record.update(status='RETAINED',finished=now(),closure_receipt=(d/'closure-receipt.json').relative_to(p).as_posix(),closure_receipt_sha256=sha256(d/'closure-receipt.json'),actual_status=summary['status'])
except Exception as error:
    record.update(status='INCOMPLETE_RETENTION',finished=now(),exception=type(error).__name__+': '+str(error))
finally:
    save(marker,record);print(json.dumps(record),flush=True)
sys.exit(0 if record['status']=='RETAINED' else 2)
