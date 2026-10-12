import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import checker
from independent import RATE

def lineage_recipe():return dict(op='independent_conditional_mean',column='sum_rate',mask='independent_both_feasible',source_kind='deterministic')
def failing_items():
 return [dict(id=f'fixture-P{i}',prediction_ref=f'P{i}',method='synthetic check',metric='synthetic fixture residual',value=0.,tolerance={'rate':RATE},verdict='FAIL' if i in [4,6] else 'PASS',triage='implementation-bug' if i in [4,6] else None,evidence_paths=['analysis/verifier-output/checks.yaml']) for i in range(1,8)]
class RoundThreeTests(unittest.TestCase):
 def test_deterministic_recipe_has_no_inferential_ci(self):
  rows=[dict(P=1,gw=1,gs=4,qw=0,qs=0,a_star=1,status='feasible')]*5
  value=checker.lineage_value(rows,lineage_recipe())
  self.assertEqual(value['n'],5);self.assertIsNone(value['statistics']['ci95']);self.assertIsNone(value['statistics']['halfwidth'])
 def test_lineage_manifest_kind_must_be_compatible(self):
  one=SimpleNamespace(scenario='x',params={'kind':'deterministic'})
  two=SimpleNamespace(scenario='x',params={'kind':'monte-carlo'})
  with self.assertRaises(ValueError):checker.validate_lineage_design([one,two],lineage_recipe())
 def test_lineage_design_cannot_claim_mc_for_fixed_cases(self):
  one=SimpleNamespace(scenario='x',params={'kind':'deterministic'})
  r=lineage_recipe();r['source_kind']='monte-carlo'
  with self.assertRaises(ValueError):checker.validate_lineage_design([one],r)
 def test_fresh_prediction_failures_retained_with_passing_checks(self):self.check_prediction_failure(False)
 def test_fresh_prediction_failures_retained_with_precision_failure(self):self.check_prediction_failure(True)
 def check_prediction_failure(self,precision):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   def reject(*args):
    d=p/'analysis/verifier-output';d.mkdir(parents=True)
    (d/'checks.yaml').write_text(json.dumps({'constraints':{'passed':True},'statistical-precision':{'passed':not precision}}))
    (d/'verification.yaml').write_text(json.dumps(failing_items()))
    raise ValueError('fixture native rejected')
   with mock.patch.object(checker,'HERE',p),mock.patch.object(checker,'require_ready_source_review',return_value={'source_hashes':{}}),mock.patch('lab.verification.verify',side_effect=reject):value=checker.run_native(p)
   self.assertEqual(value['status'],'FAIL');self.assertEqual(value['failed_native_prediction_refs'],['P4','P6']);self.assertEqual(value['failure_kind'],'numerical-contradiction')
if __name__=='__main__':unittest.main(verbosity=2)
