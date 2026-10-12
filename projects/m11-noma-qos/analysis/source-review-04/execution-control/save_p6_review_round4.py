import json,shutil
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';run=r/'.cache/p6-source-review/38dc545c799e4f5e96f7d1f15a5897cf';d=p/'analysis/source-review-04';d.mkdir()
audit=load(run/'runtime-audit.json');review=load(run/'reply.json');invocation=load(run/'invocation.json')
assert audit['enforced_independent_review'] and review['round']==4 and review['recommendation']=='ready' and not review['findings']
assert invocation['approved_packet_sha256']=='bc8ca0505fe94107ba8970f97c46c55e72cb9aa8144a5d479795978cd2c4ea9f'
for name,digest in invocation['original_hashes'].items():assert sha256(r/name.removeprefix('@repo/') if name.startswith('@repo/') else p/name)==digest
for source,target in [('reply.json','findings.json'),('runtime-audit.json','runtime-audit.json'),('invocation.json','invocation.json'),('inline-packet.json','packet.json')]:shutil.copyfile(run/source,d/target)
shutil.copyfile(r/'.cache/run_p6_source_review_round4.py',d/'run_p6_source_review_round4.py')
ids={audit['spawn_audit']['parent_thread_id'],*[c['thread_id'] for c in audit['spawn_audit']['children']]};metadata=[]
for file in (Path.home()/'.codex/sessions/2026/10/12').glob('*.jsonl'):
 with file.open(encoding='utf-8') as stream:
  first=json.loads(stream.readline()).get('payload',{})
  if first.get('id') not in ids:continue
  calls=[]
  for line in stream:
   e=json.loads(line);v=e.get('payload',{})
   if e.get('type')=='response_item' and v.get('type')=='function_call' and v.get('name','').split('.')[-1]=='spawn_agent':
    args=json.loads(v['arguments']);calls.append(dict(name=v['name'],arguments={k:args[k] for k in ['agent_type','task_name','fork_turns'] if k in args},transport_message_omitted=True))
  metadata.append(dict(session_id=first['id'],model_provider=first.get('model_provider'),cwd=first.get('cwd'),agent_role=first.get('agent_role'),spawn_calls=calls))
assert len(metadata)==2 and all(v['model_provider']=='openai' for v in metadata)
parent=next(v for v in metadata if v['session_id']==audit['spawn_audit']['parent_thread_id']);assert len(parent['spawn_calls'])==1 and parent['spawn_calls'][0]['arguments']['fork_turns']=='none'
save(d/'runtime-metadata-sanitized.json',metadata)
save(d/'receipt.json',dict(timestamp=now(),round=4,recommendation='ready',enforced_independent_review=True,scientific_acceptance=False,canonical_full_verification=False,source_hashes=invocation['original_hashes'],evidence={f.name:sha256(f) for f in d.iterdir() if f.is_file()}))
save(p/'analysis/source-review-ready.json',dict(timestamp=now(),recommendation='ready',enforced_independent_review=True,review_round=4,source_hashes=invocation['original_hashes'],review='analysis/source-review-04/findings.json',runtime_audit='analysis/source-review-04/runtime-audit.json',receipt='analysis/source-review-04/receipt.json',review_sha256=sha256(d/'findings.json'),scientific_acceptance=False,canonical_full_verification=False))
print('Enforced source-ready mapping saved for all 19 approved files; full verification not yet run.')
