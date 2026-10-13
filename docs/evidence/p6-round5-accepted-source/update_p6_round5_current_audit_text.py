import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from lab.io import load,save,sha256,now

r=Path.cwd();d=r/'docs/evidence/p6-round5-accepted-source';file=r/'docs/remaining-work-audit.md'
before=sha256(file);text=file.read_text(encoding='utf-8')
text=text.replace('The fourth enforced\nread-only source review returned READY with zero findings; its exact source\nmapping is `analysis/source-review-ready.json` under the M11 project.', 'The active source mapping now binds the fifth enforced read-only review,\nwhich returned READY with zero findings. Its exact 19-source mapping is\n`analysis/source-review-ready.json` under the M11 project. The fourth review\nand first completed verification remain retained historical evidence.')
text=text.replace('The full native verifier finished with PASS on 2026-10-12 at 16:05 UTC. Its\nreport is `projects/m11-noma-qos/analysis/verification.json`; the unique native', 'The first full native verifier finished with PASS on 2026-10-12 at 16:05 UTC.\nIts original report is now archived at `analysis/supplement/native-output-archive-attempt1/verification.json`\nunder the M11 project; the unique original native')
assert text!=file.read_text(encoding='utf-8')
file.write_text(text,encoding='utf-8',newline='\n')
scanner=Path(sys.executable).parent/'detect-secrets.exe'
result=subprocess.run([str(scanner),'scan','--all-files','docs/remaining-work-audit.md'],cwd=r,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONUTF8':'1'},check=True,timeout=120)
results=json.loads(result.stdout)['results']
assert not results,results
save(d/'post-native-text-delta-scan.json',dict(timestamp=now(),status='PASS',scope='Only scannable file changed since final native scan: current remaining-work audit text. Exact explicit-file detector scan found no detections.',file='docs/remaining-work-audit.md',before_sha256=before,after_sha256=sha256(file),detections=0,full_native_scan='PASS:2626files',scientific_source_changed=False))
shutil.copyfile(r/'.cache/update_p6_round5_current_audit_text.py',d/'update_p6_round5_current_audit_text.py')
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--','docs/remaining-work-audit.md',d.relative_to(r).as_posix()],capture_output=True,check=True)
print('Updated current source/archived-result paths; delta secret scan PASS.')
