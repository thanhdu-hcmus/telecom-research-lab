import subprocess
from pathlib import Path

r=Path.cwd();d=r/'docs/evidence/p6-attempt2-native-checkpoint';d.mkdir(exist_ok=False)
base=(r/'.cache/audit_p6_attempt2_launch_delta.py').read_text(encoding='utf-8')
base=base.replace("assert head=='fd2877faa2629e6a7cb98b82b661ed1a89108ef0'", "assert head=='39423f649d6c50fdf4b59c22f8f8e3868401bc5c'")
anchor="ready=load(p/'analysis/source-review-ready.json')"
extension="""# Rehash every actual input/output referenced by the completed fresh native report.
native_marker=load(r/'.cache/p6-canonical-attempt2-native-active.json')
assert native_marker['status']=='RECORDED' and native_marker['scientific_status']=='PASS'
native=load(p/native_marker['scientific_receipt'])
for name,digest in native['native_report']['input_hashes'].items():
    file=r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name
    assert file.resolve().is_relative_to(r.resolve()) and sha256(file)==digest,name
    add(digest,'Independently rehashed actual fresh native input/output file SHA256: '+name)
# Verified canonical decisions and actual Git ancestor objects remain public digests.
from lab.state import decisions
for value in decisions(p):add(value['record_hash'],'Verified append-only canonical gate decision hash '+value['gate'])
for commit in subprocess.check_output(g+['rev-list','HEAD'],text=True).splitlines():
    assert subprocess.check_output(g+['cat-file','-t',commit],text=True).strip()=='commit'
    add(commit,'Actual Git ancestor commit object, not authentication data.')
for directory in (p/'analysis/supplement/runs').iterdir():
    if not directory.is_dir():continue
    for value in directory.name.split('-'):
        if len(value)!=32:continue
        try:assert uuid.UUID(value).hex==value
        except (ValueError,AssertionError):continue
        add(value,'Actual scientific execution-directory UUID: '+directory.relative_to(r).as_posix())
"""
assert anchor in base;base=base.replace(anchor,extension+'\n'+anchor)
base=base.replace('p6-attempt2-launch-delta-scan','p6-attempt2-native-checkpoint-delta-scan').replace('since the fully scanned CI-passing fd2877f', 'since the CI-passing 39423f6; referenced native evidence also independently rehashed')
(r/'.cache/audit_p6_attempt2_native_checkpoint_delta.py').write_text(base,encoding='utf-8',newline='\n')
(d/'audit_p6_attempt2_native_checkpoint_delta.py').write_text(base,encoding='utf-8',newline='\n')
for name in ['prepare_p6_native_checkpoint_delta_audit.py','stage_p6_attempt2_native_checkpoint.py']:
    (d/name).write_bytes((r/'.cache'/name).read_bytes())
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',d.relative_to(r).as_posix()],capture_output=True,check=True)
print('Prepared exact delta audit with actual native evidence rehashing and unchanged detector coverage.')
