import ast
from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/run_unit_tests.py');s=p.read_text();s=s.replace('    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")}','    before = None')
s=s.replace('        source_hashes=before,','        source_hashes=None,')
s=s.replace('    try:\n        result = subprocess.run(', '    try:\n        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")}\n        receipt["source_hashes"] = before\n        result = subprocess.run(')
s=s.replace('        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")}', '''        try:
            after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")}
            unchanged = before is not None and before == after
        except Exception as exc:
            unchanged = False
            receipt["source_recheck_exception"] = type(exc).__name__ + ": " + str(exc)''')
s=s.replace('source_hashes_unchanged=before == after','source_hashes_unchanged=unchanged');s=s.replace('        if before != after:','        if not unchanged:');p.write_text(s,encoding='utf-8',newline='\n')
p=Path('projects/m11-noma-qos/analysis/supplement/test_supplement.py');s=p.read_text();s=s.replace('import replay\n','import replay\nimport run_unit_tests as runner\n');cut=s.rfind('if __name__ == "__main__":');s=s[:cut];text=Path('.cache/test_p6_runner_initialization.py').read_text(encoding='utf-8-sig');tree=ast.parse(text)
for n in tree.body:
 if isinstance(n,ast.ClassDef):s+='\n\n'+ast.get_source_segment(text,n)
s+='\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n';p.write_text(s,encoding='utf-8',newline='\n')
