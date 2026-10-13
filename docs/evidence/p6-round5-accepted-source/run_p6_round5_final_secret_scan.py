import json
import sys
from pathlib import Path
from lab.io import save
from scripts.check_secrets import check

r=Path.cwd()
report=check(r)
save(r/'.cache/p6-round5-accepted-source-native-secrets.json',report)
print(json.dumps(report))
sys.exit(report['status']!='PASS')
