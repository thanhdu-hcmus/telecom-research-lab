import hashlib,json,subprocess
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';g=['git','-c',f'safe.directory={r.as_posix()}'];raw=subprocess.run(g+['ls-files','--stage','-z'],capture_output=True,check=True).stdout;entries={}
for record in raw.split(b'\0'):
 if not record:continue
 header,name=record.split(b'\t',1);mode,object_id,stage=header.split();assert stage==b'0';entries[name.decode('utf-8')]=object_id.decode()
head_names=set(subprocess.run(g+['ls-tree','-r','--name-only','HEAD'],capture_output=True,text=True,check=True).stdout.splitlines())
changed=set(subprocess.run(g+['diff','--cached','--name-only'],capture_output=True,text=True,check=True).stdout.splitlines())
owned=[n for n in entries if n in changed or n not in head_names or n.startswith('projects/m11-noma-qos/analysis/supplement/')]
receipt=load(p/'analysis/source-review-04/receipt.json');assert receipt['recommendation']=='ready' and receipt['enforced_independent_review']
assert all(sha256(p/'analysis/source-review-04'/name)==digest for name,digest in receipt['evidence'].items())
state=load(p/'research-state.yaml');bindings={name:digest for gate in state['gates'].values() if gate['status']=='approved' for name,digest in gate.get('artifact_hashes',{}).items() if name in entries}
targets=sorted(set(owned)|set(bindings));ids=sorted({entries[n] for n in targets});data=subprocess.run(g+['cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),capture_output=True,check=True).stdout;offset=0;objects={}
for ident in ids:
 end=data.index(b'\n',offset);oid,kind,size=data[offset:end].split();assert oid.decode()==ident and kind==b'blob';length=int(size);body=data[end+1:end+1+length];assert len(body)==length;objects[ident]=hashlib.sha256(body).hexdigest();offset=end+1+length+1
mismatches=[]
for name in targets:
 staged=objects[entries[name]];working=sha256(r/name)
 if staged!=working:mismatches.append(dict(path=name,index_sha256=staged,working_sha256=working))
 if name in bindings:assert staged==bindings[name],name
assert not mismatches,mismatches[:10]
for name in entries:assert not name.endswith('/runtime-metadata.json') or not name.startswith(('projects/m11-noma-qos/analysis/source-review-02/','projects/m11-noma-qos/analysis/source-review-03/'))
lock=load(p/'sim/lock.json');assert all(sha256(r/name)==digest for name,digest in lock['input_hashes'].items())
packet=load(p/'analysis/P6-code-review-round4-payload.json');assert sha256(p/packet['packet'])==packet['packet_sha256'];assert all(sha256(r/n.removeprefix('@repo/') if n.startswith('@repo/') else p/n)==v for n,v in packet['source_hashes'].items())
report=dict(timestamp=now(),status='PASS',indexed_files_checked=len(targets),approved_index_bindings=len(bindings),owned_files_checked=len(owned),locked_inputs_checked=len(lock['input_hashes']),locked_inputs_unchanged=True,round4_packet_source_bindings_current=True,round4_review_transmitted=True,canonical_round4_source_review_ready=True,round5_review_transmitted=False,canonical_full_verification_status='COMPLETE_ATTEMPT_COMBINED_FAIL',candidate_author_diagnostic_status=load(r/'.cache/p6-candidate-full-row-diagnostic-active.json')['status'],raw_encrypted_runtime_transport_excluded=True,mismatches=mismatches)
save(r/'.cache/p6-round5-preflight-index-bindings.json',report);print(json.dumps(report))
