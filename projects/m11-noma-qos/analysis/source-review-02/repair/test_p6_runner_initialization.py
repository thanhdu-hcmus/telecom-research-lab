import sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import run_unit_tests as runner
class RunnerInitializationTests(unittest.TestCase):
 def test_initial_source_read_failure_retains_receipt(self):
  original=Path.read_bytes
  def fail(file):
   if file.name=='fixture.py':raise OSError('fixture unavailable source')
   return original(file)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'fixture.py').write_text('fixture')
   with mock.patch.object(Path,'read_bytes',fail):value=runner.run_tests(p)
   self.assertEqual(value['status'],'FAIL');self.assertIn('OSError',value['exception']);self.assertTrue((p/value['run_directory']/'receipt.json').is_file())
if __name__=='__main__':unittest.main(verbosity=2)
