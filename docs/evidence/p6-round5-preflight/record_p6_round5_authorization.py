import json,os,subprocess,tomllib
from pathlib import Path
from urllib.parse import urlparse
from lab.io import load,save,sha256,now
r=Path.cwd();p=r/'projects/m11-noma-qos';meta=load(p/'analysis/P6-code-review-round5-payload.json');packet=p/meta['packet'];assert sha256(packet)==meta['packet_sha256'] and packet.stat().st_size==406937
source_repo=r/meta['candidate_repo_relative'];source_project=source_repo/'projects/m11-noma-qos'
assert subprocess.check_output(['git','-c',f'safe.directory={source_repo.as_posix()}','rev-parse','HEAD'],cwd=source_repo,text=True).strip()=='aa68d62ac47da40a1a9f2b4890ee780d4ccb1755'
assert not (p/'analysis/P6-code-review-round5-authorization.json').exists(),'Authorization already recorded'
for name,digest in meta['source_hashes'].items():
 f=source_repo/name.removeprefix('@repo/') if name.startswith('@repo/') else source_project/name
 assert sha256(f)==digest,name
state=load(p/'research-state.yaml');assert state['phase']=='P6' and all(state['gates'][f'G{i}']['status']=='approved' for i in range(1,6))
config=tomllib.loads((Path.home()/'.codex/config.toml').read_text(encoding='utf-8'));provider=config.get('model_provider','openai');assert provider=='openai'
custom=config.get('model_providers',{}).get(provider,{}).get('base_url');assert not custom or urlparse(custom).hostname in ['api.openai.com','chatgpt.com']
for name in ['OPENAI_BASE_URL','OPENAI_API_BASE']:
 value=os.getenv(name);assert not value or urlparse(value).hostname in ['api.openai.com','chatgpt.com']
from lab.evaluation import codex_command
login=subprocess.run(codex_command()+['login','status'],capture_output=True,text=True,encoding='utf-8',timeout=30);assert login.returncode==0 and 'ChatGPT' in login.stdout+login.stderr
value=dict(timestamp=now(),user_statement='Approved',approval_context='Direct response to the exact fifth source-review authorization document and packet; one additional source-only review',candidate_commit='aa68d62ac47da40a1a9f2b4890ee780d4ccb1755',candidate_repo_relative=meta['candidate_repo_relative'],packet=meta['packet'],packet_sha256=meta['packet_sha256'],packet_bytes=406937,destination=meta['destination'],scope=meta['requested_scope'],authorized_round=5,additional_rounds=1,source_artifacts=19,illustrative_rows=24,embedded_saved_row_regression_snapshots=6,authorizes_source_review=True,authorizes_numerical_results_review=False,authorizes_scientific_gate_decisions=False,transmitted_at_record_creation=False,provider='openai',authenticated_cli='ChatGPT login verified',alternate_endpoint_detected=False)
save(p/'analysis/P6-code-review-round5-authorization.json',value)
print(json.dumps(dict(status='AUTHORIZED_INPUTS_MATCH',phase=state['phase'],gates={g:v['status'] for g,v in state['gates'].items()},packet_sha256=meta['packet_sha256'],provider=provider,login='ChatGPT verified')))
