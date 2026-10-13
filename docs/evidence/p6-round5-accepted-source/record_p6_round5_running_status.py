from pathlib import Path
from lab.io import load
from lab.state import provenance

r=Path.cwd();p=r/'projects/m11-noma-qos'
launch=load(p/'analysis/P6-code-review-round5-launch.json')
assert launch['round']==5 and launch['approved_packet_sha256']=='58b0a1787afbf47296cc66b5e8a9ccd07cdbf01152e82cb62edaddb7de8a54c4'
assert load(p/'analysis/P6-code-review-round5-explicit-authorization.json')['explicit_private_transfer_authorization']
with (p/'findings.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write('\n## P6 fifth source review explicitly authorized and running\n\nThe PI explicitly authorized sending the exact fifth private source packet to\none authenticated OpenAI Codex review session using the existing account. The\nearlier automatic-transfer rejection is historical. The launch uses the unchanged\n406,937-byte packet, candidate aa68d62, a separate read-only root and one fresh\nnamed results verifier, with no reviewer tools or writes. Effective runtime\npermissions and source integrity must be audited at completion. No numerical\nresults review or scientific gate is authorized. The active original source\nand all 51 locked inputs remain unchanged until an actual READY review.\n')
provenance(p,'Launched one explicitly PI-authorized fifth source review of the exact frozen406937-byte packet using the authenticated existing OpenAI account. Separate read-only root and fresh named reviewer; effective permissions/no-tool/source integrity audit pending completion. Earlier automatic transfer rejection superseded by explicit user authorization. Original active source, gates and51locks unchanged; numerical-results review excluded.', ['analysis/P6-code-review-round5-explicit-authorization.json','analysis/P6-code-review-round5-launch.json'],'ai')
status=p/'to_human/P6-completed-attempt-status.md'
text=status.read_text(encoding='utf-8')
text=text.replace('Candidate source review round five is prepared. The automatic approval\nreview blocked launch pending explicit authorization of the private packet\ntransfer to the existing authenticated OpenAI Codex session. No transmission\noccurred; the packet remains unchanged.', 'The PI explicitly authorized the exact private packet transfer. Source review\nround five is running in one separate authenticated OpenAI Codex session. The\nearlier automatic approval rejection is historical; the packet is unchanged.\nEffective read-only/no-tool permissions and unchanged candidate source bindings\nwill be audited at completion.')
status.write_text(text,encoding='utf-8',newline='\n')
print('Recorded explicit authorization and actual launch; runtime acceptance remains pending.')
