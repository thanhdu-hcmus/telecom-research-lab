import hashlib
import shutil
import subprocess
from pathlib import Path
from lab.io import save, now, sha256

r=Path.cwd()
d=r/'docs/evidence/p6-round5-preflight'
name='docs/evidence/p6-round5-preflight/native-secrets.json'
g=['git','-c',f'safe.directory={r.as_posix()}']
working=(r/name).read_bytes()
staged=subprocess.check_output(g+['show',':'+name])
assert b'\r\n' in working and staged==working.replace(b'\r\n',b'\n')
record=dict(timestamp=now(),status='INDEX_NEWLINE_MISMATCH_REPRODUCED',path=name,index_sha256=hashlib.sha256(staged).hexdigest(),working_sha256=hashlib.sha256(working).hexdigest(),cause='Git text normalization converted the captured native scan JSON CRLF to LF; receipt binds original captured bytes.',resolution='Preserve original native scan receipt bytes with this exact -text attribute; retain all bound receipt hashes.')
save(d/'index-newline-failure.json',record)
with (r/'.gitattributes').open('a',encoding='utf-8',newline='\n') as out:
    out.write(name+' -text whitespace=cr-at-eol,-blank-at-eof\n')
subprocess.run(g+['add','--','.gitattributes'],capture_output=True,check=True)
subprocess.run(g+['add','--renormalize','--',name],capture_output=True,check=True)
assert hashlib.sha256(subprocess.check_output(g+['show',':'+name])).hexdigest()==sha256(r/name)
shutil.copyfile(r/'.cache/preserve_p6_round5_native_scan_bytes.py',d/'preserve_p6_round5_native_scan_bytes.py')
subprocess.run(g+['add','--',d.relative_to(r).as_posix()],capture_output=True,check=True)
print('Original scan receipt bytes preserved; exact Git index match confirmed.')
