import ast
from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py');s=p.read_text()
a=s.index('    finally:\n        try:\n            report["reviewed_source_bindings_rechecked"]',s.index('def run_native'))
s=s[:a]+'''        if not stage_existed_before:
            items_path = project / "analysis/verifier-output/verification.yaml"
            if items_path.is_file():
                try:
                    from lab.models import VerificationItem
                    stage_items = [VerificationItem.model_validate(item) for item in load(items_path)]
                    if len(stage_items) != 7 or {item.prediction_ref for item in stage_items} != {"P" + str(i) for i in range(1, 8)}:
                        raise ValueError("Fresh native prediction inventory is incomplete or duplicated")
                    report["native_prediction_items"] = [item.model_dump(mode="json") for item in stage_items]
                    failed_refs = [item.prediction_ref for item in stage_items if item.verdict == "FAIL"]
                    report["failed_native_prediction_refs"] = failed_refs
                    if failed_refs:
                        report.update(status="FAIL", failure_kind="numerical-contradiction")
                except Exception as item_error:
                    report["native_prediction_item_error"] = type(item_error).__name__ + ": " + str(item_error)
                    if report.get("failure_kind") != "numerical-contradiction":
                        report.update(status="INCOMPLETE", failure_kind="native-item-integrity")
''' + s[a:]
s=s.replace('or recipe.get("column") not in {"sum_rate", "oma_sum", "paired_difference"}','or recipe.get("column") not in {"sum_rate", "oma_sum", "paired_difference"}\n        or recipe.get("source_kind") not in {"deterministic", "monte-carlo"}')
s=s.replace('        statistics=moment.summary(),','        statistics=moment.summary(recipe["source_kind"] == "deterministic"),\n        source_kind=recipe["source_kind"],')
a=s.index('def execute_lineage_recipe(')
s=s[:a]+'''def validate_lineage_design(manifests, recipe):
    """Derive the statistical design from native-validated source manifests."""
    if not manifests:
        raise ValueError("Lineage needs source manifests")
    kinds = {m.params["kind"] if hasattr(m, "params") else m["params"]["kind"] for m in manifests}
    scenarios = {m.scenario if hasattr(m, "scenario") else m["scenario"] for m in manifests}
    if len(kinds) != 1 or not kinds <= {"deterministic", "monte-carlo"} or len(scenarios) != 1:
        raise ValueError("Incompatible mixed-source statistical designs/scenarios")
    kind = next(iter(kinds))
    if recipe.get("source_kind") != kind or recipe.get("source_scenario") != next(iter(scenarios)):
        raise ValueError("Lineage recipe statistical design differs from source manifests")
    return kind == "deterministic"


''' +s[a:]
s=s.replace('        raw_files = []\n        for name in paths:', '        raw_files = []\n        source_manifests = []\n        for name in paths:')
s=s.replace('            raw = manifest_output(project, m, "channels.csv")\n            bindings','            source_manifests.append(m)\n            raw = manifest_output(project, m, "channels.csv")\n            bindings')
s=s.replace('        if bindings != recipe["input_hashes"]:\n            raise ValueError("Lineage recipe input binding mismatch")','        if bindings != recipe["input_hashes"]:\n            raise ValueError("Lineage recipe input binding mismatch")\n        receipt["deterministic"] = validate_lineage_design(source_manifests, recipe)')
s=s.replace('                mask="independent_both_feasible",\n                source_manifests=paths,','                mask="independent_both_feasible",\n                source_kind=selected[0][1]["params"]["kind"],\n                source_scenario=scenario,\n                source_manifests=paths,')
s=s.replace('            recipe_path = directory / "lineage-recipes"', '            deterministic = validate_lineage_design([m for _, m in selected], recipe)\n            recipe_path = directory / "lineage-recipes"')
s=s.replace('                    statistics=moment.summary(),','                    statistics=moment.summary(deterministic),\n                    deterministic=deterministic,')
p.write_text(s,encoding='utf-8',newline='\n')
p=Path('projects/m11-noma-qos/analysis/supplement/test_supplement.py');s=p.read_text()
s=s.replace('"mask": "independent_both_feasible",','"mask": "independent_both_feasible",\n                "source_kind": "monte-carlo",')
cut=s.rfind('if __name__ == "__main__":');s=s[:cut];text=Path('.cache/test_p6_round3_repairs.py').read_text(encoding='utf-8-sig');tree=ast.parse(text)
for n in tree.body:
 if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in {'RoundThreeTests','lineage_recipe','failing_items'}:
  segment=ast.get_source_segment(text,n).replace("source_kind='deterministic'","source_kind='deterministic',source_scenario='x'")
  s+='\n\n'+segment
s+='\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n';p.write_text(s,encoding='utf-8',newline='\n')
