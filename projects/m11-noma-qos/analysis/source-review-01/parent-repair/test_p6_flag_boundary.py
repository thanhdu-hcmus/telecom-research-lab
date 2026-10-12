import sys,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
from test_supplement import fixture,audit_fixture,oracle_fixture
import independent as ind
import replay
class FlagBoundaryTests(unittest.TestCase):
 def test_verified_serialized_strict_flag_can_cross_one_ulp(self):
  v=(1.,3.,9.,1.,2.);r,m=fixture(v)
  r['candidate_rw']=repr(math.nextafter(1.,-math.inf));r['candidate_constraints_pass']='False'
  audit=audit_fixture(r,m,v);self.assertTrue(audit.ok(),audit.counts)
  self.assertGreater(audit.diagnostic_counts.get('candidate_constraints_pass.roundoff',0),0)
 def test_material_strict_flag_discrepancy_rejected(self):
  v=(1.,3.,9.,1.,2.);r,m=fixture(v);r['candidate_rw']=repr(1.-ind.RATE/2);r['candidate_constraints_pass']='False'
  self.assertFalse(audit_fixture(r,m,v).ok())
 def test_infeasible_oracle_optimality_is_not_applicable(self):
  v=[1.,0.,0.,1.,1.];r,m=fixture(v)
  def solve(*inputs,**kw):return oracle_fixture(inputs,status='infeasible',**kw)
  base=solve(*v,rate_tolerance=ind.RATE,split_tolerance=ind.SPLIT,objective_tolerance=ind.OBJECTIVE,max_root_iterations=96,max_optimizer_iterations=256)
  check=dict(row=0,inputs=v,analytic_status='infeasible',analytic_sum=None,oracle=base)
  a=ind.Audit();out=replay.replay_job([check],[r],dict(oracle_rows=1,sensitivity_rows=0,rate_tolerance=ind.RATE,split_tolerance=ind.SPLIT,objective_tolerance=ind.OBJECTIVE),solve,a)
  self.assertEqual(out['optimality_not_established_counts']['base'],0)
  self.assertEqual(out['optimality_not_applicable_counts']['base'],1)
if __name__=='__main__':unittest.main(verbosity=2)

