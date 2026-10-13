import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from lab.io import load, save, sha256, now

r=Path.cwd()
d=r/'docs/evidence/p6-round5-preflight'
source=r/'.cache/p6-round5-preflight-secret-audit.json'
report=load(source)
assert report['status']=='FAIL' and len(report['unreviewed'])==1
shutil.copyfile(source,d/'secret-audit-initial-failure.json')
hit=report['unreviewed'][0]
assert hit['path']=='projects/m11-noma-qos/analysis/P6-code-review-round5-authorization.json'
assert hit['line_number']==5 and hit['type']=='Hex High Entropy String'
auth=load(r/hit['path'])
commit=auth['candidate_commit']
assert commit=='aa68d62ac47da40a1a9f2b4890ee780d4ccb1755'
candidate=r/auth['candidate_repo_relative']
git=['git','-c',f'safe.directory={candidate.as_posix()}','-C',str(candidate)]
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()==commit
assert subprocess.check_output(git+['cat-file','-t',commit],text=True).strip()=='commit'
assert hashlib.sha1(commit.encode()).hexdigest()==hit['hashed_secret']
baseline_path=r/'.secrets.baseline'
assert sha256(baseline_path)==report['baseline_before_sha256']
baseline=json.loads(baseline_path.read_text(encoding='utf-8'))
classified=report['new_allowlist_entries']+[dict(path=hit['path'],line=hit['line_number'],type=hit['type'],hashed_secret=hit['hashed_secret'],evidence=['Exact independently verified candidate Git HEAD commit object on fix/p6-crossing-r5; not a credential.'])]
for entry in classified:
    values=baseline['results'].setdefault(entry['path'],[])
    assert entry['hashed_secret'] not in {v['hashed_secret'] for v in values}
    values.append(dict(type=entry['type'],filename=entry['path'],line_number=entry['line'],hashed_secret=entry['hashed_secret'],is_secret=False))
baseline_path.write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8',newline='\n')
save(d/'secret-checksum-classification.json',dict(timestamp=now(),status='EXACT_CLASSIFICATION_COMPLETE',full_scan_files=report['files_scanned'],new_exact_entries=classified,unreviewed=[],baseline_before_sha256=report['baseline_before_sha256'],baseline_after_sha256=sha256(baseline_path),initial_full_audit_sha256=sha256(d/'secret-audit-initial-failure.json'),candidate_commit_object_verified=True,native_final_scan_pending=True,detector_configuration_unchanged=True,scope='Exact verified digests only; no broad exclusions. Full native scanner must still verify the resulting baseline.'))
shutil.copyfile(r/'.cache/resolve_p6_round5_preflight_checksum.py',d/'resolve_p6_round5_preflight_checksum.py')
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--','.secrets.baseline',d.relative_to(r).as_posix()],capture_output=True,check=True)
print(json.dumps(dict(status='CLASSIFIED',exact_entries=len(classified),candidate_commit_object_verified=True,final_native_scan_pending=True)))
