import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import checker
from test_supplement import native_items,complete,options
class RoundTwoTests(unittest.TestCase):
 def test_deterministic_precision_is_not_statistical_failure(self):
  s=complete();s['scenarios']['q']={'deterministic':True,'paired':{'sum_rate':{'n':5,'ci95':None,'precision_met':False}},'events':{}}
  v=checker.combined_assessment({'status':'PASS'},s,native_items(),[])
  self.assertEqual(v['failed_precision'],[])
 def test_native_timeout_does_not_establish_scientific_failure(self):
  self.assertEqual(checker.combined_assessment({'status':'INCOMPLETE','failure_kind':'timeout'},complete(),native_items(),[])['status'],'INCONCLUSIVE')
 def test_native_precision_rejection_is_inconclusive(self):
  self.assertEqual(checker.combined_assessment({'status':'FAIL','failure_kind':'statistical-precision'},complete(),native_items(),[])['status'],'INCONCLUSIVE')
 def test_actual_constraint_failure_is_scientific_fail(self):
  self.assertEqual(checker.combined_assessment({'status':'FAIL','failure_kind':'numerical-contradiction'},complete(),native_items(),[])['status'],'FAIL')
 def test_native_precision_exception_records_structured_reason(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   def failure(*args):
    (p/'analysis/verifier-output').mkdir(parents=True)
    (p/'analysis/verifier-output/checks.yaml').write_text(json.dumps({'statistical-precision':{'passed':False},'constraints':{'passed':True}}))
    raise ValueError('fixture native rejection')
   with mock.patch.object(checker,'HERE',p),mock.patch.object(checker,'require_ready_source_review',return_value={'source_hashes':{}}),mock.patch('lab.verification.verify',side_effect=failure):
    v=checker.run_native(p)
   self.assertEqual(v['failure_kind'],'statistical-precision');self.assertEqual(v['status'],'INCONCLUSIVE')
 def test_final_inventory_change_detected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'results/runs/a').mkdir(parents=True);(p/'results/runs/a/manifest.json').write_text('{}')
   before=checker.manifest_path_inventory(p)
   (p/'results/runs/b').mkdir();(p/'results/runs/b/manifest.json').write_text('{}')
   self.assertNotEqual(before,checker.manifest_path_inventory(p))
 def test_full_reviewed_dependency_change_detected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'analysis').mkdir();names=[f'file{i}.py' for i in range(19)]
   hashes={}
   for name in names:(p/name).write_text('before');hashes[name]=checker.sha256(p/name)
   (p/'analysis/P6-code-review-payload.json').write_text(json.dumps({'artifact_paths':names}))
   (p/'analysis/source-review-ready.json').write_text(json.dumps({'recommendation':'ready','enforced_independent_review':True,'source_hashes':hashes}))
   (p/names[-1]).write_text('after')
   with self.assertRaises(ValueError):checker.require_ready_source_review(p)
 def test_empty_statistical_fields_do_not_complete_coverage(self):
  self.assertFalse(checker.assessment_coverage(complete(),{},{}))
 def test_unit_runner_timeout_retains_output_and_receipt(self):
  import subprocess
  path=Path(checker.HERE/'run_unit_tests.py');spec=importlib.util.spec_from_file_location('fixture_runner',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
  with tempfile.TemporaryDirectory() as t:
   with mock.patch.object(runner.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',1,output=b'partial',stderr=b'err')):
    v=runner.run_tests(Path(t),timeout=1)
   self.assertEqual(v['status'],'FAIL');self.assertIn('TimeoutExpired',v['exception'])
   root=Path(t)/v['run_directory'];self.assertEqual((root/'stdout.txt').read_text(),'partial');self.assertTrue((root/'receipt.json').is_file())
 def test_unit_runner_missing_junit_retains_receipt(self):
  import subprocess
  path=Path(checker.HERE/'run_unit_tests.py');spec=importlib.util.spec_from_file_location('fixture_runner2',path);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
  with tempfile.TemporaryDirectory() as t:
   with mock.patch.object(runner.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'out','')):
    v=runner.run_tests(Path(t),timeout=1)
   self.assertEqual(v['status'],'FAIL');self.assertIn('FileNotFoundError',v['exception']);self.assertTrue((Path(t)/v['run_directory']/'receipt.json').is_file())
if __name__=='__main__':unittest.main(verbosity=2)
