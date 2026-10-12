import json,math,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import checker
from independent import Audit
from scipy.stats import binomtest
import independent as ind

def options(**kw):
 d=dict(max_job_seconds=3600.,max_total_seconds=86400.,max_memory_mb=1024);d.update(kw);return SimpleNamespace(**d)

class ParentReviewTests(unittest.TestCase):
 def test_probability_roundoff_interoperation(self):
  for n,k in [(10,0),(10,10),(1000,137),(393216,0),(393216,500)]:
   exact=binomtest(k,n).proportion_ci(confidence_level=.95,method='exact')
   own=ind.binomial(k,n)['ci95'];a=Audit()
   checker.compare_probability(a,'low',exact.low,own[0]);checker.compare_probability(a,'high',exact.high,own[1])
   self.assertTrue(a.ok(),a.counts)
 def test_probability_corruption_and_invalid_range(self):
  for x in [.500001,float('nan'),float('inf'),-1e-16,1+1e-15]:
   a=Audit();checker.compare_probability(a,'p',x,.5);self.assertFalse(a.ok())
 def test_limit_validation(self):
  for key in ['max_job_seconds','max_total_seconds','max_memory_mb']:
   for value in [0,-1,float('nan'),float('inf')]:
    with self.assertRaises(ValueError):checker.Budget(options(**{key:value}))
 def test_budget_deadline(self):
  with mock.patch.object(checker.time,'monotonic',return_value=0):b=checker.Budget(options(max_total_seconds=1))
  with mock.patch.object(checker.time,'monotonic',return_value=2):
   with self.assertRaises(TimeoutError):b.check()
 def test_initial_guard_failure_retains_unique_receipts(self):
  with tempfile.TemporaryDirectory() as t:
   with mock.patch.object(checker,'HERE',Path(t)),mock.patch.object(checker,'ensure_phase',side_effect=ValueError('fixture phase guard')):
    for _ in range(2):
     with self.assertRaises(ValueError):checker.execute(Path(t),options())
   receipts=list(Path(t).glob('runs/*/execution-report.json'))
   self.assertEqual(len(receipts),2)
   for f in receipts:self.assertIn('fixture phase guard',json.loads(f.read_text())['exception'])
 def test_native_timeout_retains_stdout_and_receipt(self):
  import subprocess
  with tempfile.TemporaryDirectory() as t:
   with mock.patch.object(checker,'HERE',Path(t)),mock.patch.object(checker,'require_ready_source_review',create=True),mock.patch('lab.verification.verify',side_effect=subprocess.TimeoutExpired('fixture',1,output=b'partial-out',stderr=b'partial-err')):
    report=checker.run_native(Path(t))
   self.assertEqual(report['status'],'INCOMPLETE')
   root=Path(report['run_directory']);self.assertEqual((root/'stdout.txt').read_text(),'partial-out');self.assertEqual((root/'stderr.txt').read_text(),'partial-err')
 def test_combined_keeps_declared_uncertainty_and_native_failure(self):
  native={'status':'PASS'};supp={'status':'CHECKED_WITH_DECLARED_UNRESOLVED','stored_unresolved_rows':5,'error_counts':{},'unsupported_resolved_predicates':0}
  value=checker.combined_assessment(native,supp,[],['analysis/fixture.json'])
  self.assertEqual(value['status'],'INCONCLUSIVE');self.assertFalse(value['eligible_for_gate_request'])
  self.assertTrue(any(i['verdict']=='INCONCLUSIVE' for i in value['verification_items']))
  native['status']='FAIL';self.assertEqual(checker.combined_assessment(native,supp,[],['analysis/fixture.json'])['status'],'FAIL')
 def test_combined_rejects_insufficient_precision(self):
  supp={'status':'CHECKS_COMPLETE','stored_unresolved_rows':0,'error_counts':{},'unsupported_resolved_predicates':0,'scenarios':{'x':{'paired':{'sum_rate':{'precision_met':False,'n':10}}}}}
  self.assertEqual(checker.combined_assessment({'status':'PASS'},supp,[],['analysis/fixture.json'])['status'],'INCONCLUSIVE')
 def test_lineage_executable_conditional_mask_and_undefined(self):
  rows=[dict(P=1,gw=1,gs=4,qw=0,qs=0,a_star=1,status='feasible'),dict(P=1,gw=0,gs=0,qw=1,qs=1,a_star=None,status='infeasible')]
  recipe={'op':'independent_conditional_mean','column':'sum_rate','mask':'independent_both_feasible'}
  value=checker.lineage_value(rows,recipe)
  self.assertEqual(value['n'],1);self.assertAlmostEqual(value['value'],math.log2(5));self.assertEqual(value['rows'],2)
  empty=checker.lineage_value(rows[1:],recipe);self.assertIsNone(empty['value']);self.assertEqual(empty['n'],0)
 def test_lineage_invalid_mask_rejected(self):
  with self.assertRaises(ValueError):checker.lineage_value([],{ 'op':'independent_conditional_mean','column':'sum_rate','mask':'author_flags_only'})

if __name__=='__main__':unittest.main(verbosity=2)
