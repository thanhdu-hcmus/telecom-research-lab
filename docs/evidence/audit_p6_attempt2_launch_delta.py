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
assert head=='fd2877faa2629e6a7cb98b82b661ed1a89108ef0'
assert subprocess.check_output(g+['cat-file','-t',head],text=True).strip()=='commit'
add(head,'Actual reviewed-source Git HEAD commit object; not a credential.')
for kind in ['native','supplement','assessment']:
    marker=load(r/f'.cache/p6-canonical-attempt2-{kind}-active.json')
    directory=r/marker['directory'];assert directory.is_dir()
    ident=directory.name.split('-')[0];assert uuid.UUID(ident).hex==ident
    add(ident,'Actual unique attempt2 '+kind+' control-directory UUID; not a credential.')
    for file in directory.iterdir():
        if file.is_file():add(sha256(file),'Actual local attempt2 control file SHA256: '+file.relative_to(r).as_posix())
ready=load(p/'analysis/source-review-ready.json');assert ready['review_round']==5
for name,digest in ready['source_hashes'].items():assert sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest
assert all(sha256(r/name)==digest for name,digest in load(p/'sim/lock.json')['input_hashes'].items())
path=r/'.secrets.baseline';prior=path.read_bytes();baseline=json.loads(prior)
entries=[];unknown=[];scanner=Path(sys.executable).parent/'detect-secrets.exe'
result=subprocess.run([str(scanner),'scan','--all-files',*changed],cwd=r,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},timeout=120,check=True)
for name,hits in json.loads(result.stdout)['results'].items():
    name=name.replace('\\','/');values=baseline['results'].setdefault(name,[]);existing={v['hashed_secret'] for v in values if v.get('is_secret') is False}
    for hit in hits:
        if hit['hashed_secret'] in existing:continue
        proof=known.get(hit['hashed_secret'])
        if hit['type'] not in ['Hex High Entropy String','Base64 High Entropy String'] or not proof:unknown.append(dict(path=name,**hit));continue
        values.append({**hit,'is_secret':False});existing.add(hit['hashed_secret']);entries.append(dict(path=name,line=hit['line_number'],type=hit['type'],hashed_secret=hit['hashed_secret'],evidence=proof))
report=dict(timestamp=now(),status='FAIL' if unknown else 'PASS',method='Incremental scan of every new/modified scannable staged path since the fully scanned CI-passing fd2877f. Exact digests are classified only against rehashed actual files, verified Git object or existing operation UUID directories. No broad exclusions or unknown acceptances.',scanned_paths=changed,scanned_path_hashes={n:sha256(r/n) for n in changed},new_exact_entries=entries,unreviewed=unknown,baseline_before_sha256=hashlib.sha256(prior).hexdigest(),unchanged_reviewed_sources=True,unchanged_locked_inputs=51,scientific_acceptance=False)
save(r/'.cache/p6-attempt2-launch-delta-scan.json',report)
assert not unknown,[(v['path'],v['line_number'],v['type']) for v in unknown]
assert path.read_bytes()==prior
path.write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8',newline='\n')
save(r/'docs/evidence/p6-attempt2-launch-delta-scan.json',report)
subprocess.run(g+['add','--','.secrets.baseline','docs/evidence/p6-attempt2-launch-delta-scan.json'],capture_output=True,check=True)
print(json.dumps(dict(status='PASS',scanned_paths=len(changed),new_exact_entries=len(entries),unknown_detections=0)))
