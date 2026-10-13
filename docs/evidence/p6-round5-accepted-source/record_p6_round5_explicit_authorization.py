import json
import os
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import urlparse
from lab.evaluation import codex_command
from lab.io import load,save,sha256,now
from lab.state import provenance

r=Path.cwd();p=r/'projects/m11-noma-qos'
old=load(p/'analysis/P6-code-review-round5-authorization.json')
meta=load(p/'analysis/P6-code-review-round5-payload.json')
packet=p/meta['packet']
assert sha256(packet)==old['packet_sha256']==meta['packet_sha256']=='58b0a1787afbf47296cc66b5e8a9ccd07cdbf01152e82cb62edaddb7de8a54c4'
assert packet.stat().st_size==406937
candidate=r/meta['candidate_repo_relative']
assert subprocess.check_output(['git','-c',f'safe.directory={candidate.as_posix()}','-C',str(candidate),'rev-parse','HEAD'],text=True).strip()==old['candidate_commit']
for name,digest in meta['source_hashes'].items():
    file=candidate/name.removeprefix('@repo/') if name.startswith('@repo/') else candidate/'projects/m11-noma-qos'/name
    assert sha256(file)==digest,name
config=tomllib.loads((Path.home()/'.codex/config.toml').read_text(encoding='utf-8'))
assert config.get('model_provider','openai')=='openai'
endpoint=config.get('model_providers',{}).get('openai',{}).get('base_url')
assert not endpoint or urlparse(endpoint).hostname in ['api.openai.com','chatgpt.com']
for name in ['OPENAI_BASE_URL','OPENAI_API_BASE']:
    value=os.getenv(name);assert not value or urlparse(value).hostname in ['api.openai.com','chatgpt.com']
login=subprocess.run(codex_command()+['login','status'],capture_output=True,text=True,encoding='utf-8',timeout=30)
assert login.returncode==0 and 'ChatGPT' in login.stdout+login.stderr
target=p/'analysis/P6-code-review-round5-explicit-authorization.json'
assert not target.exists() and not (p/'analysis/P6-code-review-round5-launch.json').exists()
record={**old,'timestamp':now(),'user_statement':'Authorize sending the exact fifth P6 private source-review packet to one authenticated OpenAI Codex review session using my existing account.','approval_context':'Explicit user authorization of this exact private source packet and existing-account OpenAI Codex destination after automatic approval review rejected the earlier generic Approved.','supersedes_transfer_block':'analysis/P6-code-review-round5-transfer-blocked.json','previous_authorization_sha256':sha256(p/'analysis/P6-code-review-round5-authorization.json'),'explicit_private_transfer_authorization':True,'transmitted_at_record_creation':False}
save(target,record)
provenance(p,'PI explicitly authorized sending the exact fifth P6 private source-review packet to one authenticated OpenAI Codex review session using the existing account. One source-only review of frozen packet58b0a1787afbf47296cc66b5e8a9ccd07cdbf01152e82cb62edaddb7de8a54c4; numerical-results transmission, later source reviews and scientific gates excluded.',[target.relative_to(p).as_posix()],'user')
print(json.dumps(dict(status='EXPLICIT_TRANSFER_AUTHORIZATION_RECORDED',packet_sha256=meta['packet_sha256'],packet_bytes=406937,provider='openai',login='ChatGPT verified')))
