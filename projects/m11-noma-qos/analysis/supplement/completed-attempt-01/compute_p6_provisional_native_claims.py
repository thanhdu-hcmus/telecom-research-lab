"""Compute legitimate provisional per-seed values, then check with native evaluate_claim."""
import csv,json,math
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.verification import evaluate_claim
r=Path.cwd();p=r/'projects/m11-noma-qos';plan=load(p/'analysis/claim-plan.json');assert plan['status']=='PLANNED_ONLY';records=[]
md=p/'analysis/provisional-native-claims.md';assert not md.exists();md.write_text('# Provisional per-seed arithmetic\n\nThese values are local arithmetic checks, not accepted manuscript claims.\nCombined P6 assessment is FAIL and G6/G7 remain invalidated.\nEach example is seed 11001, zero QoS, 32,768 draws; none pools seeds.\n\n',encoding='utf-8',newline='\n')
for item in plan['claims']:
 spec=json.loads(item['computation']);manifest=p/item['source_manifest'];assert sha256(manifest)==item['source_manifest_sha256'];values=[]
 with (p/spec['path']).open(encoding='utf-8',newline='') as f:
  for raw in csv.DictReader(f):values.append(float(raw[spec['column']]))
 assert len(values)==item['scope']['draws'] and all(math.isfinite(v) for v in values)
 if spec['op']=='mean':value=math.fsum(values)/len(values)
 elif spec['op']=='count':value=math.fsum(values)
 else:raise ValueError('Unapproved planned native operation')
 claim={k:item[k] for k in ['key','unit','source_manifest','computation']};claim.update(value=value,used_in=['analysis/provisional-native-claims.md']);checked=evaluate_claim(p,claim)
 assert math.isclose(value,checked['value'],rel_tol=1e-10,abs_tol=1e-12)
 records.append(dict(claim=claim,scope=item['scope'],arithmetic_check=checked,status='COMPUTED_NOT_SCIENTIFICALLY_ACCEPTED'))
 with md.open('a',encoding='utf-8',newline='\n') as f:f.write(f"- `{item['key']}`: {checked['value']:.15g} {item['unit']}; manifest `{item['source_manifest']}`; operation `{spec['op']}` on `{spec['column']}`.\n")
report=dict(timestamp=now(),status='PROVISIONAL_ARITHMETIC_VERIFIED',scientific_acceptance=False,registered_manuscript_claims=False,native_arithmetic_checks=9,claims=records,combined_assessment_status='FAIL',source_plan_sha256=sha256(p/'analysis/claim-plan.json'),limits=['Single seed per setting; zero QoS only; no pooled or conditional native claims.','Read-only native evaluate_claim was invoked with independently computed actual values, not fabricated probes.','No results/claims.json registration or gate approval.','Global scientific acceptance awaits repair, canonical verification, independent results review and PI decision.'])
save(p/'analysis/provisional-native-claims.json',report);print(json.dumps(dict(status=report['status'],count=len(records),scientific_acceptance=False)))
