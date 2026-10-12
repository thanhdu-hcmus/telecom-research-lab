import ast
from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py');s=p.read_text();a=s.index('def write_lineage');b=s.index('def init_scenario',a);part=s[a:b].replace('statistics=moment.summary(recipe["source_kind"] == "deterministic"),','statistics=moment.summary(deterministic),\n                    deterministic=deterministic,');s=s[:a]+part+s[b:];p.write_text(s,encoding='utf-8',newline='\n')
p=Path('projects/m11-noma-qos/analysis/supplement/test_supplement.py');s=p.read_text();a=s.rfind('if __name__ == "__main__":');method='''
class DeterministicLineageExecutionTests(unittest.TestCase):
    def test_written_record_and_executed_recipe_suppress_deterministic_ci(self):
        import csv
        with tempfile.TemporaryDirectory() as t:
            project = Path(t)
            run = project / "results/runs/fixture"
            run.mkdir(parents=True)
            raw = run / "channels.csv"
            row = dict(P=1, gw=1, gs=4, qw=0, qs=0, a_star=1, status="feasible")
            with raw.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
                writer.writerows([row] * 5)
            manifest = dict(scenario="fixture", params={"kind": "deterministic"}, outputs=[dict(path=raw.relative_to(project).as_posix(), sha256=checker.sha256(raw))])
            mf = run / "manifest.json"
            checker.save(mf, manifest)
            summary = checker.init_scenario()
            summary["total"] = 5
            summary["independent_counts"]["n11"] = 5
            for moment in summary["independent_pairs"].values():
                for value in range(5):
                    moment.add(float(value))
            out = project / "analysis/lineage-fixture"
            checker.write_lineage(project, [(mf, manifest)], {"fixture": summary}, out, Audit())
            records = checker.load(out / "claim-lineage.json")["records"]
            for record in records:
                self.assertEqual(record["n"], 5)
                self.assertIsNone(record["statistics"]["ci95"])
                self.assertIsNone(record["statistics"]["halfwidth"])
            recipe = checker.load(project / records[0]["recipe_path"])
            with mock.patch.object(checker, "HERE", project / "analysis/supplement"), mock.patch.object(checker, "require_ready_source_review", return_value={"source_hashes": {}}), mock.patch.object(checker, "verify_manifest", return_value=SimpleNamespace(scenario="fixture", params={"kind": "deterministic"})), mock.patch.object(checker, "manifest_output", return_value=raw):
                result = checker.execute_lineage_recipe(project, recipe, options())
            self.assertEqual(result["n"], 5)
            self.assertAlmostEqual(result["value"], math.log2(5))
            self.assertIsNone(result["statistics"]["ci95"])
            self.assertIsNone(result["statistics"]["halfwidth"])
            self.assertTrue(result["deterministic"])


'''
s=s[:a]+method+s[a:];p.write_text(s,encoding='utf-8',newline='\n')
