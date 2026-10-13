import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from lab.io import load,save,sha256,now
from scripts.check_secrets import EXCLUDED

r=Path.cwd();p=r/'projects/m11-noma-qos';g=['git','-c',f'safe.directory={r.as_posix()}']
inventory=[n for n in subprocess.check_output(g+['ls-files','-z'],text=True).split('\0') if n]
changed=[n for n in subprocess.check_output(g+['diff','--cached','--name-only','--diff-filter=ACM'],text=True).splitlines() if not EXCLUDED.search(n)]
assert changed and all((r/n).is_file() for n in changed)
known={}
def add(value,proof):known[hashlib.sha1(value.encode()).hexdigest()]=proof
for name in inventory:add(sha256(r/name),'Actual current tracked file SHA256: '+name)
head=subprocess.check_output(g+['rev-parse','HEAD'],text=True).strip()
assert head=='79cf29ff82f27112ef4142a8c84cc2f3ae0691fe'
assert subprocess.check_output(g+['cat-file','-t',head],text=True).strip()=='commit'
add(head,'Actual reviewed-source Git HEAD commit object; not a credential.')
for kind in ['native','supplement','assessment']:
    marker=load(r/f'.cache/p6-canonical-attempt2-{kind}-active.json')
    directory=r/marker['directory'];assert directory.is_dir()
    ident=directory.name.split('-')[0];assert uuid.UUID(ident).hex==ident
    add(ident,'Actual unique attempt2 '+kind+' control-directory UUID; not a credential.')
    for file in directory.iterdir():
        if file.is_file():add(sha256(file),'Actual local attempt2 control file SHA256: '+file.relative_to(r).as_posix())
# Rehash every actual input/output referenced by the completed fresh native report.
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

ready=load(p/'analysis/source-review-ready.json');assert ready['review_round']==5
for name,digest in ready['source_hashes'].items():assert sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest
assert all(sha256(r/name)==digest for name,digest in load(p/'sim/lock.json')['input_hashes'].items())
raw=r/'.cache/p6-results-review-preparation/unfiltered-native-results-review-local-only.md';assert raw.is_file();add(sha256(raw),'Actual locally retained unfiltered packet SHA256; no private transmission.')
for packet_name in ['numerical-review-01-packet.json','numerical-review-01-deterministic-packet.json']:
    packet=load(p/'analysis'/packet_name)
    for name,binding in packet['artifact_bindings'].items():
        body=packet['files'][name].encode('utf-8');assert len(body)==binding['bytes'];assert hashlib.sha256(body).hexdigest()==binding['sha256']
        if binding.get('derived'):
            add(binding['sha256'],'Independently rehashed explicitly labelled in-packet derived artifact '+name)
path=r/'.secrets.baseline';working_baseline=path.read_bytes();prior=subprocess.check_output(g+['show','HEAD:.secrets.baseline']);baseline=json.loads(prior)
entries=[];unknown=[];scanner=Path(sys.executable).parent/'detect-secrets.exe'
result=subprocess.run([str(scanner),'scan','--all-files',*changed],cwd=r,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},timeout=120,check=True)
for name,hits in json.loads(result.stdout)['results'].items():
    name=name.replace('\\','/');values=baseline['results'].setdefault(name,[]);existing={v['hashed_secret'] for v in values if v.get('is_secret') is False}
    for hit in hits:
        if hit['hashed_secret'] in existing:continue
        proof=known.get(hit['hashed_secret'])
        if hit['type'] not in ['Hex High Entropy String','Base64 High Entropy String'] or not proof:unknown.append(dict(path=name,**hit));continue
        values.append({**hit,'is_secret':False});existing.add(hit['hashed_secret']);entries.append(dict(path=name,line=hit['line_number'],type=hit['type'],hashed_secret=hit['hashed_secret'],evidence=proof))
report=dict(timestamp=now(),status='FAIL' if unknown else 'PASS',method='Incremental scan of every new/modified scannable staged path since the CI-passing 79cf29f; referenced native evidence also independently rehashed. Exact digests are classified only against rehashed actual files, verified Git object or existing operation UUID directories. No broad exclusions or unknown acceptances.',scanned_paths=changed,scanned_path_hashes={n:sha256(r/n) for n in changed},new_exact_entries=entries,unreviewed=unknown,baseline_before_sha256=hashlib.sha256(prior).hexdigest(),unchanged_reviewed_sources=True,unchanged_locked_inputs=51,scientific_acceptance=False)
save(r/'.cache/p6-attempt2-completed/digest-classifications.json',report)
assert not unknown,[(v['path'],v['line_number'],v['type']) for v in unknown]
assert path.read_bytes()==working_baseline
working_entries=json.loads(working_baseline)['results'];working_false={n:{v['hashed_secret'] for v in values if v.get('is_secret') is False} for n,values in working_entries.items()}
assert all(v['hashed_secret'] in working_false.get(n,set()) for n,values in baseline['results'].items() for v in values if v.get('is_secret') is False)
save(r/'docs/evidence/p6-attempt2-completed/digest-classifications.json',report)
subprocess.run(g+['add','--','docs/evidence/p6-attempt2-completed/digest-classifications.json'],capture_output=True,check=True)
print(json.dumps(dict(status='PASS',scanned_paths=len(changed),new_exact_entries=len(entries),unknown_detections=0)))
