import io,json,math,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import checker
from independent import oma, rates

def options():return SimpleNamespace(max_job_seconds=3600.,max_total_seconds=86400.,max_memory_mb=1024)
def native_items():return [dict(prediction_ref=f'P{i}',verdict='PASS') for i in range(1,8)]
def complete():return dict(status='CHECKS_COMPLETE',error_counts={},stored_unresolved_rows=0,unsupported_resolved_predicates=0,bindings_rechecked=True,source_bindings_rechecked=True,jobs=[dict(rows=4718692,replay=dict(base=4708,tighter=1160))]+[dict(rows=0,replay=dict(base=0,tighter=0)) for _ in range(144)],scenarios={'q':{'paired':{},'events':{},'deterministic':False}},oracle_unresolved_counts={},oracle_optimality_not_established_counts={})
class AdditionalReceiptTests(unittest.TestCase):
 def test_combined_oracle_uncertainty_is_not_pass(self):
  s=complete();s['oracle_unresolved_counts']={'base':1}
  self.assertEqual(checker.combined_assessment({'status':'PASS'},s,native_items(),[])['status'],'INCONCLUSIVE')
 def test_combined_missing_binding_or_coverage_is_not_pass(self):
  for field in ['bindings_rechecked','source_bindings_rechecked','jobs','scenarios']:
   s=complete();del s[field]
   self.assertEqual(checker.combined_assessment({'status':'PASS'},s,native_items(),[])['status'],'INCONCLUSIVE')
 def test_combined_false_binding_is_fail(self):
  s=complete();s['bindings_rechecked']=False
  self.assertEqual(checker.combined_assessment({'status':'PASS'},s,native_items(),[])['status'],'FAIL')
 def test_combined_positive_low_event_precision_is_inconclusive(self):
  s=complete();s['scenarios']['q']['events']={'noma_infeasibility':{'events':50,'minimum_events_met':False,'zero_event_upper_bound':None}}
  self.assertEqual(checker.combined_assessment({'status':'PASS'},s,native_items(),[])['status'],'INCONCLUSIVE')
 def test_lineage_rejects_equal_gain_interior_endpoint(self):
  r=dict(P=1,gw=1,gs=1,qw=0,qs=0,a_star=.5,status='feasible')
  with self.assertRaisesRegex(ValueError,'endpoint'):checker.lineage_value([r],{'op':'independent_conditional_mean','column':'sum_rate','mask':'independent_both_feasible'})
 def test_lineage_guard_failure_has_unique_receipts(self):
  with tempfile.TemporaryDirectory() as t:
   with mock.patch.object(checker,'HERE',Path(t)),mock.patch.object(checker,'require_ready_source_review',side_effect=ValueError('fixture source guard')):
    for _ in range(2):
     with self.assertRaises(ValueError):checker.execute_lineage_recipe(Path(t),{},options())
   files=list(Path(t).glob('runs/*/lineage-receipt.json'));self.assertEqual(len(files),2)
   self.assertTrue(all('fixture source guard' in json.loads(f.read_text())['exception'] for f in files))
 def test_independent_lineage_moment_excludes_unsupported_stored_mask(self):
  inputs=[1.,1.,4.,0.,0.]; od=oma(inputs);nr=rates(inputs,1.)
  checked=(inputs,{'status':'unresolved'},'feasible','n11',nr['sum_rate']-od['oma_sum'],od,{'fixed_feasible':0,'grid_found_feasible':0})
  s=checker.init_scenario();checker.update(s,{'a_star':'1','candidate_violation':'False','status':'feasible'},checked)
  self.assertEqual(s['independent_pairs']['sum_rate'].n,0)
  self.assertEqual(s['pairs']['sum_rate'].n,1)
if __name__=='__main__':unittest.main(verbosity=2)
