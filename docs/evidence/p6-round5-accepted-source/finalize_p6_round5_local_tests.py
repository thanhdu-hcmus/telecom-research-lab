import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from lab.io import load,save,sha256,now

r=Path.cwd();p=r/'projects/m11-noma-qos';d=r/'docs/evidence/p6-round5-accepted-source'
tree=ET.parse(r/'.cache/p6-round5-integrated-framework-tests.xml')
suites=list(tree.getroot().iter('testsuite'))
totals={key:sum(int(suite.attrib.get(key,'0')) for suite in suites) for key in ['tests','failures','errors','skipped']}
assert totals==dict(tests=97,failures=0,errors=0,skipped=0),totals
for suffix,target in [('tests.xml','framework-tests.xml'),('stdout.txt','framework-stdout.txt'),('stderr.txt','framework-stderr.txt')]:
    shutil.copyfile(r/f'.cache/p6-round5-integrated-framework-{suffix}',d/target)
save(d/'framework-test-receipt.json',dict(timestamp=now(),status='PASS',**totals,elapsed_s=sum(float(s.attrib.get('time','0')) for s in suites),command='python -m pytest -q --basetemp .cache/pytest-p6-round5-integrated --junitxml .cache/p6-round5-integrated-framework-tests.xml',evidence={name:sha256(d/name) for name in ['framework-tests.xml','framework-stdout.txt','framework-stderr.txt']},scientific_acceptance=False))
initial=d/'prepare_p6_round5_acceptance_checkpoint.py'
shutil.copyfile(initial,d/'prepare_p6_round5_acceptance_checkpoint-initial.py')
save(d/'initial-staging-failure.json',dict(timestamp=now(),status='GIT_ADD_REJECTED_IGNORED_LOG',initial_helper_sha256=sha256(initial),ignored_path='projects/m11-noma-qos/analysis/supplement/unit-tests.log',cause='.gitignore line17 excludes *.log.',resolution='Keep the log local; stdout/stderr/JUnit/receipt are already retained in the actual unique unit run. Remove only that redundant ignored log from the stage list. No science input or source changed.'))
script=r/'.cache/prepare_p6_round5_acceptance_checkpoint.py'
script.write_text(script.read_text(encoding='utf-8').replace(",'projects/m11-noma-qos/analysis/supplement/unit-tests.log'",''),encoding='utf-8',newline='\n')
shutil.copyfile(script,initial)
local=load(d/'local-checks.json');save(d/'local-checks.json',{**local,'timestamp':now(),'framework_suite':'PASS','framework_tests':97,'framework_test_receipt_sha256':sha256(d/'framework-test-receipt.json')})
for file in [p/'findings.md',p/'to_human/P6-completed-attempt-status.md']:
    text=file.read_text(encoding='utf-8').replace('The framework suite is running.', 'All 97 framework tests pass.').replace('the framework suite\nis running.', 'all 97 framework tests\npass.')
    file.write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(r/'.cache/finalize_p6_round5_local_tests.py',d/'finalize_p6_round5_local_tests.py')
cr=[file.relative_to(r).as_posix() for file in d.rglob('*') if file.is_file() and b'\r\n' in file.read_bytes()]
if cr:
    with (r/'.gitattributes').open('a',encoding='utf-8',newline='\n') as out:out.write('\n# Preserve exact local round5 framework test capture.\n'+''.join(name+' -text whitespace=cr-at-eol,-blank-at-eof\n' for name in cr))
paths=[d.relative_to(r).as_posix(),'projects/m11-noma-qos/findings.md','projects/m11-noma-qos/to_human/P6-completed-attempt-status.md']+(['.gitattributes'] if cr else [])
subprocess.run(['git','-c',f'safe.directory={r.as_posix()}','add','--',*paths],capture_output=True,check=True)
print(json.dumps(dict(status='LOCAL_TESTS_PASS',framework_tests=97,supplement_tests=133,failures=0,errors=0)))
