import json
import shutil
from pathlib import Path
from lab.io import load, save, sha256, now
from lab.state import provenance

r = Path.cwd()
p = r / 'projects/m11-noma-qos'
source = r / '.cache/p6-full-candidate-audit/6393ed4d41914d239b24cb9900ea26c5'
record = load(source / 'diagnostic-receipt.json')
assert record['status'] == 'COMPLETE' and record['errors'] == 0
assert record['completed_jobs'] == 145 and record['completed_rows'] == 4718692
assert record['source_bindings_unchanged'] and record['locked_inputs_unchanged']
assert not record['canonical_execution'] and not record['scientific_acceptance']
for name, digest in record['evidence'].items():
    assert sha256(source / name) == digest
jobs = [json.loads(line) for line in (source / 'jobs.jsonl').read_text().splitlines()]
assert len(jobs) == 145 and sum(j['rows'] for j in jobs) == 4718692
assert all(not j['error_counts'] and not j['errors'] for j in jobs)
assert sum(len(j['ambiguities']) for j in jobs) == 10
meta = load(p / 'analysis/P6-code-review-round5-payload.json')
candidate = r / meta['candidate_repo_relative']
for name, digest in meta['source_hashes'].items():
    assert sha256(candidate / name.removeprefix('@repo/') if name.startswith('@repo/') else candidate / 'projects/m11-noma-qos' / name) == digest
for name, digest in load(p / 'sim/lock.json')['input_hashes'].items():
    assert sha256(r / name) == digest
ready = load(p / 'analysis/source-review-ready.json')
assert ready['review_round'] == 4
for name, digest in ready['source_hashes'].items():
    assert sha256(r / name.removeprefix('@repo/') if name.startswith('@repo/') else p / name) == digest
assert not (p / 'analysis/P6-code-review-round5-launch.json').exists()
d = p / 'analysis/supplement/candidate-round5-author-diagnostic'
d.mkdir(exist_ok=False)
for f in source.iterdir():
    if f.is_file():
        shutil.copyfile(f, d / f.name)
shutil.copyfile(r / '.cache/run_p6_full_candidate_row_diagnostic.py', d / 'run_p6_full_candidate_row_diagnostic.py')
shutil.copyfile(r / '.cache/retain_p6_round5_preflight.py', d / 'retain_p6_round5_preflight.py')
save(d / 'retention-receipt.json', dict(timestamp=now(), status='AUTHOR_DIAGNOSTIC_COMPLETE', jobs=145, rows=4718692, row_errors=0, scientific_acceptance=False, canonical_execution=False, ambiguities_preserved=sum(len(j['ambiguities']) for j in jobs), candidate_source_hashes=meta['source_hashes'], canonical_source_hashes=ready['source_hashes'], locked_inputs_unchanged=True, evidence={f.name:sha256(f) for f in d.iterdir() if f.is_file()}))
blocked = dict(timestamp=now(), status='AUTO_REVIEW_REJECTED_BEFORE_LAUNCH', action='Launch one external fifth P6 source review', transmitted=False, reviewer_launched=False, packet_sha256=meta['packet_sha256'], packet_bytes=meta['packet_bytes'], destination=meta['destination'], reason='Available user message is only Approved, without trusted explicit authorization of this private payload and destination.', required_action='Obtain explicit user authorization naming this exact private packet transfer to the existing authenticated OpenAI Codex session; do not bypass rejection.', authorization_record='analysis/P6-code-review-round5-authorization.json', authorization_record_sha256=sha256(p/'analysis/P6-code-review-round5-authorization.json'))
save(p / 'analysis/P6-code-review-round5-transfer-blocked.json', blocked)
provenance(p, 'User said Approved in response to the exact fifth source-review request. Scope recorded as one source-only review of the specified packet; numerical-results transmission and scientific gates excluded. Automatic approval review rejected external launch for insufficient explicit payload/destination wording. No review was launched or packet transmitted; explicit authorization requested.', ['analysis/P6-code-review-round5-authorization.json', 'analysis/P6-code-review-round5-transfer-blocked.json'], 'joint')
with (p / 'findings.md').open('a', encoding='utf-8', newline='\n') as out:
    out.write('\n## P6 candidate author diagnostic complete; fifth transfer blocked\n\nThe isolated candidate checked every saved row: 145 jobs / 4,718,692 rows,\nzero row errors, with source and all 51 locked-input bindings unchanged.\nTen recorded deterministic method ambiguities remain explicit. This author\ndiagnostic omits canonical integrity guards, shared oracle replays and global\nstatistics; it is not canonical verification or scientific acceptance.\nEvidence is retained in analysis/supplement/candidate-round5-author-diagnostic.\n\nThe PI responded Approved to the fifth source-review request. The automatic\napproval review rejected the external launch because the available message\ndid not explicitly name the private payload and destination. No packet was\ntransmitted and no reviewer launched. Explicit transfer authorization has been\nrequested. The original round-four source remains active, its completed FAIL\nremains recorded, and G6/G7 remain invalidated.\n')
status = p / 'to_human/P6-completed-attempt-status.md'
text = status.read_text(encoding='utf-8')
text = text.replace('Candidate source review round five remains\npending under the exact packet already prepared.', 'Candidate source review round five is prepared. The automatic approval\nreview blocked launch pending explicit authorization of the private packet\ntransfer to the existing authenticated OpenAI Codex session. No transmission\noccurred; the packet remains unchanged.')
text = text.replace('An author check of every saved row with the candidate is running.', 'The candidate author diagnostic completed all 145 jobs / 4,718,692 rows\nwith zero row errors and unchanged source and locked-input bindings. Ten\ndeterministic method ambiguities remain; this is not canonical acceptance.')
status.write_text(text, encoding='utf-8', newline='\n')
audit = r / 'docs/remaining-work-audit.md'
text = audit.read_text(encoding='utf-8')
text = text.replace('P6 still needs complete discrepancy triage, any necessary repair/rerun, combined\nassessment, executable manuscript claims and enforced independent results review.', 'Complete discrepancy triage is retained. The candidate author diagnostic has\ncompleted all 145 jobs / 4,718,692 rows with zero row errors; it retains the\ndeterministic ambiguities and omits canonical guards, shared replay and global\nstatistics. The automatic approval review rejected the fifth external review\nlaunch pending explicit private-packet/destination authorization. No review\nwas launched or transmitted.\n\nP6 still needs independent candidate source review, the corrected canonical\nrerun and combined assessment, executable accepted manuscript claims, and\nenforced independent numerical-results review.')
audit.write_text(text, encoding='utf-8', newline='\n')
provenance(p, 'Retained complete candidate author diagnostic: 145 jobs and 4,718,692 saved rows, zero row errors, ten deterministic method ambiguity entries preserved; all19 canonical source bindings, all19 candidate bindings and all51 locked inputs unchanged. Author-only diagnostic excludes production guards/shared replay/global statistics and cannot establish scientific acceptance. Original completed combined FAIL and source-ready round4 retained; fifth external review blocked before transmission.', ['analysis/supplement/candidate-round5-author-diagnostic/retention-receipt.json', 'analysis/P6-code-review-round5-transfer-blocked.json', 'to_human/P6-completed-attempt-status.md'], 'ai')
print(json.dumps(dict(status='RETAINED',jobs=145,rows=4718692,row_errors=0,ambiguity_entries=sum(len(j['ambiguities']) for j in jobs),source_review_transmitted=False)))
