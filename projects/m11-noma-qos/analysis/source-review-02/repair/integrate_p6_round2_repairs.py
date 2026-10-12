import ast
from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py');s=p.read_text()
s=s.replace('    reviewed = None\n    try:\n        reviewed = require_ready_source_review(project)["source_hashes"]','    reviewed = None\n    stage_existed_before = (project / "analysis/verifier-output").exists()\n    report["stage_existed_before"] = stage_existed_before\n    try:\n        reviewed = require_ready_source_review(project)["source_hashes"]')
s=s.replace('        if checks_path.is_file():','        if not stage_existed_before and checks_path.is_file():')
s=s.replace('    directory = new_run_directory("lineage")\n    sources','    directory = new_run_directory("lineage")\n    started = time.monotonic()\n    sources')
s=s.replace('            finished=now(), peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1]','            finished=now(), runtime_s=time.monotonic() - started, peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1]')
p.write_text(s,encoding='utf-8',newline='\n')
p=Path('.cache/test_p6_round2_repairs.py');s=p.read_text();a=s.index(' def test_native_precision_exception_records_structured_reason');b=s.index(' def test_final_inventory',a)
s=s[:a]+''' def test_native_precision_exception_records_structured_reason(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   def failure(*args):
    (p/'analysis/verifier-output').mkdir(parents=True)
    (p/'analysis/verifier-output/checks.yaml').write_text(json.dumps({'statistical-precision':{'passed':False},'constraints':{'passed':True}}))
    raise ValueError('fixture native rejection')
   with mock.patch.object(checker,'HERE',p),mock.patch.object(checker,'require_ready_source_review',return_value={'source_hashes':{}}),mock.patch('lab.verification.verify',side_effect=failure):
    v=checker.run_native(p)
   self.assertEqual(v['failure_kind'],'statistical-precision');self.assertEqual(v['status'],'INCONCLUSIVE')
''' + s[b:];p.write_text(s,encoding='utf-8',newline='\n')
p=Path('projects/m11-noma-qos/analysis/supplement/test_supplement.py');s=p.read_text();s=s.replace('import copy\n','import copy\nimport importlib.util\n');s=s.replace('        native["status"] = "FAIL"','        native["status"] = "FAIL"\n        native["failure_kind"] = "numerical-contradiction"')
cut=s.rfind('if __name__ == "__main__":');assert cut>0;s=s[:cut]
for filename,names in [('test_p6_round2_repairs.py',{'RoundTwoTests'}),('test_p6_round2_coverage.py',{'shaped_coverage','RoundTwoCoverageTests'})]:
 text=(Path('.cache')/filename).read_text(encoding='utf-8-sig');tree=ast.parse(text)
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names:s+='\n\n'+ast.get_source_segment(text,n)
s+='\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n';p.write_text(s,encoding='utf-8',newline='\n')
