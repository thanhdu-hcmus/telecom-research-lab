import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import checker
from test_supplement import options,native_items

def shaped_coverage():
 jobs={'a':dict(rows=5,base=2,tighter=1),'b':dict(rows=5,base=2,tighter=1)}
 scens={'q':dict(rows=10,deterministic=True)}
 counts=dict(n00=0,n01=0,n10=0,n11=10,unresolved=0)
 stat=dict(n=10,mean=1.,variance=0.,ci95=None,halfwidth=None,relative_halfwidth=None,precision_met=False)
 value=dict(deterministic=True,N_total=10,N_resolved=10,unresolved=0,counts=counts,independent_counts=counts.copy(),paired={key:stat.copy() for key in ['sum_rate','oma_sum','paired_difference']},events={},ablations={'fixed':{},'grid':{}})
 supp=dict(status='CHECKS_COMPLETE',jobs=[dict(run_id=name,rows=x['rows'],replay=dict(base=x['base'],tighter=x['tighter'])) for name,x in jobs.items()],scenarios={'q':value})
 return supp,jobs,scens
class RoundTwoCoverageTests(unittest.TestCase):
 def test_shaped_exact_inventory_is_accepted(self):
  s,j,c=shaped_coverage();self.assertTrue(checker.assessment_coverage(s,j,c))
 def test_redistributed_job_totals_rejected(self):
  s,j,c=shaped_coverage();s['jobs'][0]['rows']=6;s['jobs'][1]['rows']=4;self.assertFalse(checker.assessment_coverage(s,j,c))
 def test_wrong_scenario_identity_rejected(self):
  s,j,c=shaped_coverage();s['scenarios']['wrong']=s['scenarios'].pop('q');self.assertFalse(checker.assessment_coverage(s,j,c))
 def test_empty_scenario_statistics_rejected(self):
  s,j,c=shaped_coverage();s['scenarios']['q']['paired']={};self.assertFalse(checker.assessment_coverage(s,j,c))
 def test_stale_native_checks_do_not_describe_new_failed_attempt(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'analysis/verifier-output').mkdir(parents=True)
   (p/'analysis/verifier-output/checks.yaml').write_text(json.dumps({'constraints':{'passed':False}}))
   with mock.patch.object(checker,'HERE',p),mock.patch.object(checker,'require_ready_source_review',return_value={'source_hashes':{}}),mock.patch('lab.verification.verify',side_effect=ValueError('previous stage exists')):
    value=checker.run_native(p)
   self.assertEqual(value['status'],'INCOMPLETE');self.assertNotEqual(value.get('failure_kind'),'numerical-contradiction')
 def test_final_deadline_is_accounted_and_retained(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);clock=[0.];calls=[0];original_load=checker.load
   def snapshots(*args,**kw):
    calls[0]+=1
    if calls[0]==2:clock[0]=100.
    return {}
   with mock.patch.object(checker,'HERE',p),mock.patch.object(checker.time,'monotonic',side_effect=lambda:clock[0]),mock.patch.object(checker,'ensure_phase'),mock.patch.object(checker,'require_ready_source_review',return_value={'source_hashes':{}}),mock.patch.object(checker,'locked',return_value=({'scenarios':[]},{})),mock.patch.object(checker,'read_inventory',return_value=[]),mock.patch.object(checker,'check_jobs'),mock.patch.object(checker,'input_snapshot',side_effect=snapshots),mock.patch.object(checker,'load',side_effect=lambda f:{'cases':[]} if Path(f).name=='cases.yaml' else original_load(f)):
    with self.assertRaisesRegex(ValueError,'deterministic table coverage'):checker.execute(p,options(max_total_seconds=50))
   report=json.loads(next(p.glob('runs/*/execution-report.json')).read_text())
   self.assertEqual(report['status'],'INCOMPLETE');self.assertIn('deadline',report['binding_error']);self.assertEqual(report['runtime_s'],100.)
if __name__=='__main__':unittest.main(verbosity=2)
