import ast
from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py');s=p.read_text()
s=s.replace('    root = project.parents[1]\n    for name', '''    if not isinstance(ready.get("source_hashes"), dict) or len(ready["source_hashes"]) != 19:
        raise ValueError("Source review must bind the full approved 19-source inventory")
    expected = load(project / "analysis/P6-code-review-payload.json")["artifact_paths"]
    if set(ready["source_hashes"]) != set(expected):
        raise ValueError("Source review inventory differs from approved packet")
    root = project.parents[1]
    for name''')
s=s.replace('and bool(supplement.get("scenarios"))','and len(supplement.get("scenarios", {})) == 13')
s=s.replace('        report["oracle_optimality_not_established_counts"] = {','''        report["oracle_optimality_not_applicable_counts"] = {
            kind: sum(r["replay"]["optimality_not_applicable_counts"][kind] for r in records)
            for kind in ("independent", "base", "tighter")
        }
        report["oracle_optimality_not_established_counts"] = {''')
p.write_text(s,encoding='utf-8',newline='\n')
p=Path('projects/m11-noma-qos/analysis/supplement/test_supplement.py');s=p.read_text();cut=s.rfind('if __name__ == "__main__":');assert cut>0;s=s[:cut]
for name,keep in [('test_p6_additional_receipts.py',{'native_items','complete','AdditionalReceiptTests'}),('test_p6_flag_boundary.py',{'FlagBoundaryTests'}),('test_p6_source_coverage.py',{'SourceCoverageTests'})]:
 src=Path('.cache')/name;text=src.read_text(encoding='utf-8-sig');tree=ast.parse(text)
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in keep:
   block=ast.get_source_segment(text,n)
   block=block.replace('od=oma(inputs)','od=ind.oma(inputs)')
   if n.name=='complete':block=block.replace("scenarios={'q':{'paired':{},'events':{},'deterministic':False}}","scenarios={key:{'paired':{},'events':{},'deterministic':False} for key in ['q']+[f'fixture-{i}' for i in range(12)]}")
   s+='\n\n'+block
s+='\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n';p.write_text(s,encoding='utf-8',newline='\n')
