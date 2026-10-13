import csv
import json
import math
from pathlib import Path
from lab.io import load,save,sha256,now
from lab.verification import evaluate_claim

r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/supplement/attempt2-native-checkpoint'
marker=load(r/'.cache/p6-canonical-attempt2-native-active.json')
assert marker['status']=='RECORDED' and marker['scientific_status']=='PASS'
native=p/marker['scientific_receipt'];assert sha256(native)==marker['scientific_receipt_sha256']
plan=load(p/'analysis/claim-plan.json');assert plan['status']=='PLANNED_ONLY'
md=d/'provisional-native-claims.md';assert not md.exists()
relative=md.relative_to(p).as_posix()
md.write_text('# Current-attempt provisional native arithmetic\n\nFresh native verification passed. The full supplement and combined assessment\nare still pending. These nine single-seed zero-QoS examples are author arithmetic\nchecks; they are not registered or scientifically accepted manuscript claims.\n\n',encoding='utf-8',newline='\n')
records=[]
old=load(p/'analysis/provisional-native-claims.json')
prior={item['claim']['key']:item['arithmetic_check']['value'] for item in old['claims']}
for item in plan['claims']:
    spec=json.loads(item['computation']);manifest=p/item['source_manifest']
    assert sha256(manifest)==item['source_manifest_sha256']
    with (p/spec['path']).open(encoding='utf-8',newline='') as file:
        values=[float(row[spec['column']]) for row in csv.DictReader(file)]
    assert len(values)==32768 and len(values)==item['scope']['draws'] and all(math.isfinite(v) for v in values)
    if spec['op']=='mean':value=math.fsum(values)/len(values)
    elif spec['op']=='count':value=math.fsum(values)
    else:raise ValueError('Unexpected planned native operation')
    claim={key:item[key] for key in ['key','unit','source_manifest','computation']}
    claim.update(value=value,used_in=[relative])
    checked=evaluate_claim(p,claim)
    assert math.isclose(value,checked['value'],rel_tol=1e-10,abs_tol=1e-12)
    assert checked['value']==prior[item['key']]
    records.append(dict(claim=claim,scope=item['scope'],arithmetic_check=checked,unchanged_from_first_attempt_arithmetic=True,status='COMPUTED_NOT_SCIENTIFICALLY_ACCEPTED'))
    with md.open('a',encoding='utf-8',newline='\n') as out:
        out.write(f"- `{item['key']}`: {checked['value']:.15g} {item['unit']}; seed11001, {item['scope']['scenario']},32768draws.\n")
assert len(records)==9
save(d/'provisional-native-claims.json',dict(timestamp=now(),status='CURRENT_NATIVE_ARITHMETIC_REVALIDATED',scientific_acceptance=False,registered_manuscript_claims=False,native_arithmetic_checks=9,native_receipt=marker['scientific_receipt'],native_receipt_sha256=marker['scientific_receipt_sha256'],source_review_round=5,combined_assessment_status='PENDING_CURRENT_ATTEMPT',source_plan_sha256=sha256(p/'analysis/claim-plan.json'),prior_provisional_receipt_sha256=sha256(p/'analysis/provisional-native-claims.json'),claims=records,limits=['Single seed per setting; zero QoS only; no pooled or conditional native claims.','Actual values independently computed with math.fsum and checked through unmodified native evaluate_claim with ordinary manifest/output guards.','No results/claims.json registration or scientific gate decision.','The original provisional arithmetic record is preserved.']))
print(json.dumps(dict(status='REVALIDATED',arithmetic_checks=9,values_unchanged=True,scientific_acceptance=False)))
