"""Validate local packet scope and original/derived bytes; never transmit."""
import hashlib,json
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';packet=load(p/'analysis/numerical-review-01-deterministic-packet.json');metadata=load(p/'analysis/numerical-review-01-deterministic-payload.json')
assert sha256(p/metadata['packet'])==metadata['packet_sha256'] and (p/metadata['packet']).stat().st_size==metadata['packet_bytes']
assert len(packet['files'])==metadata['artifacts']==32 and not metadata['external_transmission_performed']
assert packet['review_scope']==metadata['scope'] and not packet['bulk_monte_carlo_raw_rows_enclosed'] and not packet['all_full_result_reports_enclosed']
original=0;derived=0
for name,content in packet['files'].items():
 body=content.encode('utf-8');binding=packet['artifact_bindings'][name]
 assert hashlib.sha256(body).hexdigest()==binding['sha256'] and len(body)==binding['bytes']
 if binding.get('derived'):
  v=json.loads(content);source=load(p/v['origin']);assert sha256(p/v['origin'])==v['origin_sha256']
  if name=='derived/deterministic-supplement-view.json':
   assert v['deterministic_jobs']==[j for j in source['jobs'] if j['rows']==100]
   assert v['deterministic_scenarios']=={n:s for n,s in source['scenarios'].items() if s['deterministic']}
   for field in ['status','stored_unresolved_rows','unsupported_resolved_predicates','oracle_base_statuses','oracle_unresolved_counts','oracle_optimality_not_established_counts','error_counts']:assert v[field]==source[field]
  elif name=='derived/deterministic-lineage-view.json':assert v['records']==[j for j in source['records'] if j['source_kind']=='deterministic']
  else:raise AssertionError(name)
  derived+=1
 else:
  f=r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name;assert body==f.read_bytes();original+=1
 assert not any(x in name for x in ['source-review-','author-diagnostic','author-certificate','provisional-native','completed-attempt-','attempt2-launch','to_human','unit-test-results','lint-results','runtime-metadata','findings.md','ara/trace'])
ready=load(p/'analysis/source-review-ready.json');assert all(sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n)==d for n,d in ready['source_hashes'].items())
assert all(sha256(r/n)==d for n,d in load(p/'sim/lock.json')['input_hashes'].items())
assert original==30 and derived==2
metadata_sizing=metadata['offline_sizing'];assert metadata_sizing['estimate_fits_prior_root_child_route'] and metadata_sizing['twice_packet_tokens_plus_50000_reserve']<metadata_sizing['observed_prior_same_model_context_window']
report=dict(timestamp=now(),status='PASS',packet=metadata['packet'],packet_sha256=metadata['packet_sha256'],original_artifact_bytes_verified=original,explicit_derived_views_verified=derived,source_bindings_current=19,locked_inputs_unchanged=51,author_narratives_and_previous_reviews_excluded=True,scope='Deterministic stress-case/certificate handling; bulk Monte Carlo acceptance not reviewed',external_transmission=False,scientific_acceptance=False,sizing_is_explicit_encoding_estimate=True)
save(p/'analysis/numerical-review-preparation/scoped-packet-validation.json',report)
print(json.dumps(report))
