import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
import checker
class SourceCoverageTests(unittest.TestCase):
 def test_ready_review_cannot_omit_source_inventory(self):
  with tempfile.TemporaryDirectory() as t:
   project=Path(t);(project/'analysis').mkdir()
   (project/'analysis/source-review-ready.json').write_text(json.dumps(dict(recommendation='ready',enforced_independent_review=True,source_hashes={})))
   with self.assertRaises(ValueError):checker.require_ready_source_review(project)
if __name__=='__main__':unittest.main(verbosity=2)
