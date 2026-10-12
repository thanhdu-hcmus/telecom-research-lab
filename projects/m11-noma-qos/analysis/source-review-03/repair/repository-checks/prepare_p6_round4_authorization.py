import json,shutil
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';d=p/'analysis/source-review-03/repair';d.mkdir(exist_ok=True)
for name in ['test_p6_round3_repairs.py','p6-round3-red.txt','repair_p6_round3.py','verify_p6_deterministic_lineage.py']:
 shutil.copyfile(r/'.cache'/name,d/name)
supp=p/'analysis/supplement';tests=load(supp/'unit-test-results.json');sources={f.name:sha256(f) for f in supp.glob('*.py')};assert tests['status']=='PASS' and tests['source_hashes']==sources
lock=load(p/'sim/lock.json');assert all(sha256(r/n)==h for n,h in lock['input_hashes'].items())
save(d/'checkpoint.json',dict(timestamp=now(),status='REPAIRS_TESTED_ADDITIONAL_SOURCE_REVIEW_AUTHORIZATION_REQUIRED',source_hashes=sources,tests=tests,locked_inputs_checked=51,locked_inputs_unchanged=True,canonical_full_execution=False,authorized_source_rounds_consumed=3,repairs={'R3-F01':'Recipes record statistical design and scenario derived from source manifests. Mixed or inconsistent designs/scenarios fail. Both generated deterministic records and executed recipes suppress CI/halfwidth but retain descriptive mean/n.','R3-F02':'Fresh native stage VerificationItems validated, complete P1-P7 inventory enforced, failed references retained. P4/P6 failure is reported alongside precision failure. Pre-existing stage evidence excluded.'},evidence_hashes={f.name:sha256(f) for f in d.iterdir() if f.is_file()}))
packet=load(p/'analysis/P6-code-review-packet.json')
for name in packet['files']:
 f=r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name
 text=f.read_text(encoding='utf-8')
 if not name.startswith('analysis/supplement/'):assert text==packet['files'][name],name
 else:packet['files'][name]=text
assert len(packet['files'])==19 and sum(len(x['illustrative_rows']) for x in packet['illustrative_manifest_bound_samples'])==24
file=p/'analysis/P6-code-review-round4-packet.json';save(file,packet)
hashes={n:sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n) for n in packet['files']}
meta=dict(timestamp=now(),status='PREPARED_ONLY_NOT_AUTHORIZED_NOT_TRANSMITTED',packet=file.relative_to(p).as_posix(),packet_sha256=sha256(file),packet_bytes=file.stat().st_size,source_hashes=hashes,source_artifacts=19,illustrative_rows=24,raw_example_manifests=3,whole_raw_dataset_included=False,prior_approved_packet_sha256='4c0991c42bac89a188c460cd8433709b86ce8443c654ead71512a54c41ab0111',destination='Separate authenticated OpenAI Codex review session using the existing account',requested_scope='One additional enforced read-only artifact-only source review (round 4), of this exact packet. Reviewer uses no tools or writes. Later numerical-results review and scientific gate decisions are excluded.',excluded=['Credentials','PDFs','Full raw dataset','Author reasoning or repair narrative','Earlier reviews','Provenance','Test verdicts'])
save(p/'analysis/P6-code-review-round4-payload.json',meta)
(p/'to_human/P6-additional-source-review-authorization.md').write_text(f'''# Approval for one additional P6 source review

Three authorized enforced source reviews are complete. Their recommendations
were REVISE. The third found two remaining analysis issues: deterministic claim
lineage generated confidence intervals, and native failure receipts omitted
failed prediction items. Both have analysis-only repairs and regression tests.
All 117 isolated JUnit cases pass. The 51 locked inputs are unchanged.

## Exact proposed transmission

- Packet: `{meta['packet']}`
- SHA256: `{meta['packet_sha256']}`
- Size: {meta['packet_bytes']:,} bytes
- Contents: the same 19 approved source paths and the same 24 illustrative rows
  from three manifest examples. Only analysis source changed.
- Destination: separate authenticated OpenAI Codex review session on the existing
  account.
- Scope: exactly one additional source-review round. Fresh read-only root,
  approval never, MCP disabled, one named fresh results_verifier at depth one;
  reviewer has no tools or writes, with actual runtime/source audit retained.

Credentials, PDFs, whole raw data, author narratives, prior reviews, provenance
and test verdicts are excluded. This approval does not authorize scientific
acceptance or an external numerical-results review. No additional review has
been launched. Full canonical verification awaits source readiness.

Reply “Approve the fourth P6 source review” to authorize this exact packet and
scope. The earlier three-round approval cannot authorize this extra round.
''',encoding='utf-8',newline='\n')
print(json.dumps({k:meta[k] for k in ['status','packet_sha256','packet_bytes','source_artifacts','illustrative_rows']}))
