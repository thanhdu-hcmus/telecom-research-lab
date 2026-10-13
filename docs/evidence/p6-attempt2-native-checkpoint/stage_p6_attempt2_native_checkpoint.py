import subprocess
from pathlib import Path
from lab.io import load

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/attempt2-native-checkpoint'
marker=load(r/'.cache/p6-canonical-attempt2-native-active.json')
audit=r/'docs/remaining-work-audit.md';text=audit.read_text(encoding='utf-8')
text=text.replace('The fresh corrected native and supplemental canonical runs are active, with\nan automatic combined-assessment watcher. Their completion remains pending.', 'The fresh corrected native verifier completed PASS on 2026-10-13 at08:27 UTC\nwith all eight checks and seven prediction items passing. The full supplement\nis active and the automatic combined-assessment watcher is waiting. An\nauthor-only exact sqrt(2)-1 certificate explains the five fractional-boundary\nrepeats; their stored unresolved labels remain unchanged. Nine provisional\nnative arithmetic examples have been revalidated; no manuscript claims were\nregistered. Full corrected scientific acceptance remains pending.')
audit.write_text(text,encoding='utf-8',newline='\n')
paths=['docs/remaining-work-audit.md','projects/m11-noma-qos/findings.md','projects/m11-noma-qos/to_human/P6-completed-attempt-status.md','projects/m11-noma-qos/ara/trace/sessions/session_index.yaml','projects/m11-noma-qos/ara/trace/sessions/2026-10-13-0044.yaml','projects/m11-noma-qos/analysis/supplement/attempt2-native-checkpoint',str((p/marker['scientific_receipt']).parent.relative_to(r)).replace('\\','/'),'projects/m11-noma-qos/analysis/verifier-output','projects/m11-noma-qos/analysis/verification.json','projects/m11-noma-qos/analysis/verification.yaml','projects/m11-noma-qos/analysis/verification-report.md']
cr=[file.relative_to(r).as_posix() for base in [d,(p/marker['scientific_receipt']).parent] for file in base.rglob('*') if file.is_file() and b'\r\n' in file.read_bytes()]
if cr:
    with (r/'.gitattributes').open('a',encoding='utf-8',newline='\n') as out:out.write('\n# Preserve exact completed attempt2 native evidence bytes.\n'+''.join(name+' -text whitespace=cr-at-eol,-blank-at-eof\n' for name in cr))
    paths.append('.gitattributes')
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',*paths],capture_output=True,check=True)
print(f'Staged native checkpoint paths; {len(cr)} CRLF evidence files preserved. Active partial supplement is excluded.')
