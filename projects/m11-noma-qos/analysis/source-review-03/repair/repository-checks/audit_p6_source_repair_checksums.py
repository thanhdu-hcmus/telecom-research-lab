import hashlib,json,os,subprocess,sys
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.state import decisions
from scripts.check_secrets import EXCLUDED
r=Path.cwd();p=r/'projects/m11-noma-qos';g=['git','-c',f'safe.directory={r.as_posix()}'];inventory=[n for n in subprocess.run(g+['ls-files','-z'],capture_output=True,text=True,check=True).stdout.split('\0') if n];files=sorted(n for n in inventory if not EXCLUDED.search(n));baseline_path=r/'.secrets.baseline';baseline=load(baseline_path);prior=baseline_path.read_bytes();known={}
def add(value,proof):known.setdefault(hashlib.sha1(value.encode()).hexdigest(),proof)
for n in inventory:
 f=r/n
 if f.is_file():add(sha256(f),'Actual current tracked working-file SHA256: '+n)
for root in (r/'.cache/p6-source-review').iterdir():
 if not root.is_dir():continue
 add(root.name,'Actual source-review UUID directory; not a credential: '+root.relative_to(r).as_posix())
 for f in root.rglob('*'):
  if f.is_file():add(sha256(f),'Actual locally retained review input/runtime file SHA256: '+f.relative_to(r).as_posix())
for n,d in load(p/'analysis/supplement/preparation.json')['inputs'].items():
 assert sha256(p/n)==d,n
 add(d,'Actual independently rehashed preparation input/output SHA256: projects/m11-noma-qos/'+n)
for d in decisions(p):add(d['record_hash'],'Validated append-only canonical gate decision hash '+d['gate'])
for commit in subprocess.run(g+['rev-list','HEAD'],capture_output=True,text=True,check=True).stdout.splitlines():
 assert subprocess.run(g+['cat-file','-t',commit],capture_output=True,text=True,check=True).stdout.strip()=='commit'
 add(commit,'Actual Git ancestor commit object')
for n in ['m11-p5-secret-audit.json','m11-p6-secret-audit.json','m11-p5-rerun-secret-audit-results.json','m11-p6-local-preparation-secret-audit.json']:
 rel='docs/evidence/'+n;blob=subprocess.run(g+['show','edacda2:'+rel],capture_output=True,check=True).stdout;assert hashlib.sha256(blob).hexdigest()==sha256(r/rel)
 old=json.loads(blob);assert old['status']=='PASS'
 for entry in old['new_allowlist_entries']:known.setdefault(entry['hashed_secret'],'Exact historical digest with immutable classified proof edacda2:'+rel+'; '+str(entry['evidence']))
new=[];unknown=[];scanner=r/'.venv/Scripts/detect-secrets.exe'
for start in range(0,len(files),36):
 result=subprocess.run([str(scanner),'scan','--all-files',*files[start:start+36]],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},check=True,timeout=120)
 for name,hits in json.loads(result.stdout)['results'].items():
  name=name.replace('\\','/');existing={v['hashed_secret'] for v in baseline['results'].get(name,[]) if v.get('is_secret') is False}
  for hit in hits:
   if hit['hashed_secret'] in existing:continue
   proof=known.get(hit['hashed_secret'])
   if hit['type']!='Hex High Entropy String' or not proof:unknown.append({'path':name,**hit});continue
   baseline['results'].setdefault(name,[]).append({**hit,'is_secret':False});existing.add(hit['hashed_secret']);new.append({'path':name,'line':hit['line_number'],'type':hit['type'],'hashed_secret':hit['hashed_secret'],'evidence':[proof]})
report=dict(timestamp=now(),status='FAIL' if unknown else 'PASS',files_scanned=len(files),method='Exact checksum/UUID classifications against actual current bytes, rehashed preparation outputs, retained review inputs, actual Git objects, canonical decision chain or unchanged historical classified proofs. Unknown detections never accepted. Existing baseline entries/configuration retained; no broad type/path exclusion.',new_allowlist_entries=new,unreviewed=unknown,canonical_scientific_verification=False,baseline_before_sha256=hashlib.sha256(prior).hexdigest())
save(r/'.cache/p6-source-repair-secret-audit.json',report)
if not unknown:
 assert baseline_path.read_bytes()==prior
 baseline_path.write_text(json.dumps(baseline,indent=2)+'\n',encoding='utf-8',newline='\n')
 save(r/'docs/evidence/m11-p6-source-repair-secret-audit.json',report)
print(json.dumps(dict(status=report['status'],files_scanned=len(files),new_exact_entries=len(new),unreviewed_count=len(unknown),unreviewed=[{k:v[k] for k in ['path','line_number','type']} for v in unknown[:15]])))
sys.exit(bool(unknown))
