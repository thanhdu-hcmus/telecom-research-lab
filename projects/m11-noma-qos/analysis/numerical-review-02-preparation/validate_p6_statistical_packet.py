"""Validate the complete local statistical packet selection and normalized views."""
import hashlib,json
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';packet=load(p/'analysis/numerical-review-02-statistical-packet.json');metadata=load(p/'analysis/numerical-review-02-statistical-payload.json')
assert sha256(p/metadata['packet'])==metadata['packet_sha256'] and (p/metadata['packet']).stat().st_size==metadata['packet_bytes']
assert len(packet['files'])==metadata['artifacts']==24 and not metadata['external_transmission_authorized'] and not metadata['external_transmission_performed']
originals=0;views=0
for name,content in packet['files'].items():
 raw=content.encode('utf-8');binding=packet['artifact_bindings'][name];assert hashlib.sha256(raw).hexdigest()==binding['sha256'] and len(raw)==binding['bytes']
 if not binding['derived']:
  f=r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name;assert raw==f.read_bytes();originals+=1
 else:
  v=json.loads(content);src=load(p/v['origin']);assert sha256(p/v['origin'])==v['origin_sha256'];data=v['data']
  if name=='derived/monte-carlo-scenario-statistics.json':
   assert data==dict(scenarios={n:s for n,s in src['scenarios'].items() if not s['deterministic']},oma_reference=src['oma_reference'])
  elif name=='derived/native-checks.json':
   expanded={k:v for k,v in data.items() if k not in ['common_check_evidence_paths','checks']}
   expanded['checks']={n:{k:v for k,v in c.items() if k!='evidence_paths_ref'}|dict(evidence_paths=data[c['evidence_paths_ref']]) for n,c in data['checks'].items()}
   assert expanded=={k:v for k,v in src.items() if k!='input_hashes'}
  elif name=='derived/monte-carlo-job-coverage.json':
   expected=[{k:j[k] for k in ['run_id','rows','row_error_count','independent_counts','ambiguity_entries','unsupported_resolved_predicates']}|dict(base_replays=j['replay']['base'],tighter_replays=j['replay']['tighter']) for j in src['jobs'] if j['rows']!=100]
   assert data==expected and len(data)==144 and sum(j['rows'] for j in data)==4718592
  elif name=='derived/monte-carlo-lineage.json':
   expanded=[]
   for scenario,group in data.items():
    for record in group['records']:
     recipe=group['common_recipe_fields']|dict(column=record['recipe_column']);assert load(p/record['recipe_path'])==recipe and sha256(p/record['recipe_path'])==record['recipe_sha256']
     expanded.append({k:v for k,v in record.items() if k not in ['recipe_column','recipe_sha256']}|dict(recipe=recipe))
   expected=[v for v in src['records'] if v['source_kind']=='monte-carlo'];assert len(expanded)==len(expected)==36
   assert {v['key']:v for v in expanded}=={v['key']:v for v in expected}
  else:raise AssertionError(name)
  views+=1
 assert not any(token in name for token in ['source-review-','numerical-review-01/','author-diagnostic','author-certificate','provisional-native','to_human','findings.md','unit-test-results','runtime-metadata','ara/trace'])
ready=load(p/'analysis/source-review-ready.json');assert all(sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n)==h for n,h in ready['source_hashes'].items());assert all(sha256(r/n)==h for n,h in load(p/'sim/lock.json')['input_hashes'].items())
assert originals==20 and views==4 and metadata['offline_sizing']['estimate_fits_prior_root_child_route']
import sys
sys.path.insert(0,str(p/'analysis/supplement'))
from checker import validate_assessment_inputs
closure=load(p/'analysis/supplement/completed-attempt-02/closure-receipt.json')
_,_,_,coverage=validate_assessment_inputs(p,p/closure['scientific_receipts']['native'],p/closure['scientific_receipts']['supplement'])
assert coverage['status']=='PASS'
save(p/'analysis/numerical-review-02-preparation/validation.json',dict(timestamp=now(),status='PASS',packet_sha256=metadata['packet_sha256'],packet_bytes=metadata['packet_bytes'],original_artifacts_verified=20,normalized_views_reconstructed_exactly=4,monte_carlo_scenarios=12,reported_jobs=144,reported_rows=4718592,exact_lineage_records_reconstructed=36,author_narratives_and_previous_reviews_excluded=True,source_bindings_current=19,locked_inputs_unchanged=51,completed_native_supplement_input_guards_rechecked=True,bulk_rows_enclosed=False,external_transmission=False,scientific_acceptance=False))
print({'status':'PASS','original_artifacts':20,'exact_normalized_views':4,'lineage_records':36,'transmitted':False})
