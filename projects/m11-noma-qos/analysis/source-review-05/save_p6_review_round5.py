import json
import shutil
from pathlib import Path
from lab.io import load,save,sha256,now

r=Path.cwd();p=r/'projects/m11-noma-qos'
launch=load(p/'analysis/P6-code-review-round5-launch.json')
run=r/launch['run'];d=p/'analysis/source-review-05'
audit=load(run/'runtime-audit.json');review=load(run/'reply.json');invocation=load(run/'invocation.json')
assert audit['enforced_independent_review'] and review['round']==5
assert review['recommendation'] in ['ready','revise','blocked']
assert invocation['approved_packet_sha256']=='58b0a1787afbf47296cc66b5e8a9ccd07cdbf01152e82cb62edaddb7de8a54c4'
candidate=r/invocation['candidate_repo_relative']
for name,digest in invocation['original_hashes'].items():
    assert sha256(candidate/name.removeprefix('@repo/') if name.startswith('@repo/') else candidate/'projects/m11-noma-qos'/name)==digest
d.mkdir(exist_ok=False)
for source,target in [('reply.json','findings.json'),('runtime-audit.json','runtime-audit.json'),('invocation.json','invocation.json'),('inline-packet.json','packet.json')]:
    shutil.copyfile(run/source,d/target)
shutil.copyfile(r/'.cache/run_p6_source_review_round5.py',d/'run_p6_source_review_round5.py')
shutil.copyfile(r/'.cache/save_p6_review_round5.py',d/'save_p6_review_round5.py')
ids={audit['spawn_audit']['parent_thread_id'],*[c['thread_id'] for c in audit['spawn_audit']['children']]};metadata=[]
dates={invocation['started'][:10],audit['finished'][:10]}
session_files=[file for date in dates for file in (Path.home()/'.codex/sessions'/date[:4]/date[5:7]/date[8:10]).glob('*.jsonl')]
for file in session_files:
    with file.open(encoding='utf-8') as stream:
        first=json.loads(stream.readline()).get('payload',{})
        if first.get('id') not in ids:continue
        calls=[]
        for line in stream:
            event=json.loads(line);value=event.get('payload',{})
            if event.get('type')=='response_item' and value.get('type')=='function_call' and value.get('name','').split('.')[-1]=='spawn_agent':
                args=json.loads(value['arguments']);calls.append(dict(name=value['name'],arguments={k:args[k] for k in ['agent_type','task_name','fork_turns'] if k in args},transport_message_omitted=True))
        metadata.append(dict(session_id=first['id'],model_provider=first.get('model_provider'),cwd=first.get('cwd'),agent_role=first.get('agent_role'),spawn_calls=calls))
assert len(metadata)==2 and all(v['model_provider']=='openai' for v in metadata)
parent=next(v for v in metadata if v['session_id']==audit['spawn_audit']['parent_thread_id'])
assert len(parent['spawn_calls'])==1 and parent['spawn_calls'][0]['arguments']['fork_turns']=='none'
save(d/'runtime-metadata-sanitized.json',metadata)
save(d/'receipt.json',dict(timestamp=now(),round=5,recommendation=review['recommendation'],enforced_independent_review=True,scientific_acceptance=False,canonical_full_verification=False,candidate_only=True,candidate_commit=invocation['candidate_commit'],source_hashes=invocation['original_hashes'],evidence={f.name:sha256(f) for f in d.iterdir() if f.is_file()}))
if review['recommendation']=='ready':
    assert not any(f.get('severity') in ['major','critical'] and f.get('status')=='open' for f in review['findings'])
    save(d/'candidate-ready.json',dict(timestamp=now(),recommendation='ready',enforced_independent_review=True,review_round=5,candidate_only=True,candidate_commit=invocation['candidate_commit'],source_hashes=invocation['original_hashes'],review='analysis/source-review-05/findings.json',runtime_audit='analysis/source-review-05/runtime-audit.json',receipt='analysis/source-review-05/receipt.json',review_sha256=sha256(d/'findings.json'),scientific_acceptance=False,canonical_full_verification=False))
print(json.dumps(dict(status='REVIEW_RETAINED',recommendation=review['recommendation'],findings=review['findings'],active_canonical_source_unchanged=True)))
