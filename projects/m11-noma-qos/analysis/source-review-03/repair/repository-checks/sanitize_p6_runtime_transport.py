import hashlib,json,subprocess
from pathlib import Path
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';g=['git','-c',f'safe.directory={r.as_posix()}']
for i in [2,3]:
 d=p/f'analysis/source-review-{i:02d}';raw=d/'runtime-metadata.json';v=load(raw)
 for entry in v:
  for call in entry.get('spawn_calls',[]):
   args=call['arguments'];message=args.pop('message',None)
   if message is not None:args['message_sha256']=hashlib.sha256(message.encode()).hexdigest();args['message_omitted']='Encrypted transport content retained only in local runtime evidence; role/fork audit is published.'
 save(d/'runtime-metadata-sanitized.json',dict(timestamp=now(),original_runtime_metadata_sha256=sha256(raw),metadata=v,redaction='Only encrypted spawn-message transport argument omitted; effective policies and role/fork fields retained.'))
 subprocess.run(g+['rm','--cached','--ignore-unmatch','--',raw.relative_to(r).as_posix()],capture_output=True,check=True)
ig=r/'.gitignore';s=ig.read_text();s+='\n# Encrypted runtime spawn-message transport is local evidence; sanitized metadata is committed.\nprojects/m11-noma-qos/analysis/source-review-02/runtime-metadata.json\nprojects/m11-noma-qos/analysis/source-review-03/runtime-metadata.json\n';ig.write_text(s,encoding='utf-8',newline='\n')
print('Opaque runtime message transport retained locally; sanitized role/permission metadata prepared.')
