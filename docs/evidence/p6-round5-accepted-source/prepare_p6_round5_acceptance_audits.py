import subprocess
from pathlib import Path

r=Path.cwd();d=r/'docs/evidence/p6-round5-accepted-source'
audit=(r/'.cache/audit_p6_round5_preflight_checksums.py').read_text(encoding='utf-8').replace('p6-round5-preflight-secret-audit','p6-round5-accepted-source-secret-audit')
needle='# Actual completed scientific-directory UUIDs, never credentials.'
extension='''# Verify the actual candidate commit object, never classify an unexplained digest.
candidate_repo=r/'.cache/worktrees/p6-crossing-r5'
candidate_git=['git','-c',f'safe.directory={candidate_repo.as_posix()}','-C',str(candidate_repo)]
candidate_commit=subprocess.check_output(candidate_git+['rev-parse','HEAD'],text=True).strip()
assert candidate_commit=='aa68d62ac47da40a1a9f2b4890ee780d4ccb1755'
assert subprocess.check_output(candidate_git+['cat-file','-t',candidate_commit],text=True).strip()=='commit'
add(candidate_commit,'Exact verified candidate Git HEAD commit object, not authentication data.')
# Actual authenticated review session identifiers, independently matched to local metadata.
metadata=load(p/'analysis/source-review-05/runtime-metadata-sanitized.json')
session_ids={v['session_id'] for v in metadata};verified_sessions=set()
for file in (Path.home()/'.codex/sessions/2026/10/13').glob('*.jsonl'):
 with file.open(encoding='utf-8') as stream: first=json.loads(stream.readline()).get('payload',{})
 if first.get('id') in session_ids:
  assert first.get('model_provider')=='openai'
  add(first['id'],'Actual OpenAI review session UUID matched against native local session metadata; not a credential.')
  verified_sessions.add(first['id'])
assert verified_sessions==session_ids and len(session_ids)==2
'''
assert needle in audit;audit=audit.replace(needle,extension+'\n'+needle)
audit=audit.replace("[p/'analysis/supplement/runs',r/'.cache/p6-canonical']", "[p/'analysis/supplement/runs',p/'analysis/supplement/unit-runs',r/'.cache/p6-canonical']")
(r/'.cache/audit_p6_round5_accepted_source_checksums.py').write_text(audit,encoding='utf-8',newline='\n')
(d/'audit_p6_round5_accepted_source_checksums.py').write_text(audit,encoding='utf-8',newline='\n')
index=(r/'.cache/check_p6_round5_preflight_index.py').read_text(encoding='utf-8').replace('p6-round5-preflight-index-bindings','p6-round5-accepted-source-index-bindings')
index=index.replace("receipt=load(p/'analysis/source-review-04/receipt.json')", "receipt=load(p/'analysis/source-review-05/receipt.json')").replace("p/'analysis/source-review-04'/name", "p/'analysis/source-review-05'/name")
index=index.replace("packet=load(p/'analysis/P6-code-review-round4-payload.json')", "packet=load(p/'analysis/P6-code-review-round5-payload.json')")
index=index.replace("round4_packet_source_bindings_current=True,round4_review_transmitted=True,canonical_round4_source_review_ready=True,round5_review_transmitted=False,canonical_full_verification_status='COMPLETE_ATTEMPT_COMBINED_FAIL'", "round5_packet_source_bindings_current=True,round5_review_transmitted=True,canonical_round5_source_review_ready=True,canonical_full_verification_status='CORRECTED_SOURCE_READY_CANONICAL_RERUN_PENDING'")
anchor="report=dict(timestamp=now()"
check="archive=load(p/'analysis/supplement/native-output-archive-attempt1/archive-receipt.json');assert all(sha256(p/archive['original_to_archive'][name])==digest for name,digest in archive['original_file_hashes'].items())\n"
assert anchor in index;index=index.replace(anchor,check+anchor)
(r/'.cache/check_p6_round5_accepted_source_index.py').write_text(index,encoding='utf-8',newline='\n')
(d/'check_p6_round5_accepted_source_index.py').write_text(index,encoding='utf-8',newline='\n')
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',d.relative_to(r).as_posix()],capture_output=True,check=True)
print('Prepared exact checksum classifiers and reviewed-source/archive index audits.')
