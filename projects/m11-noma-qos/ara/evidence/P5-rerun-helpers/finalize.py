"""Synchronize current progress only after the fresh native G5 request passes."""
from pathlib import Path
import subprocess
from lab.io import load, save, now

repo=Path.cwd().resolve()
p=repo/'projects/m11-noma-qos'
state=load(p/'research-state.yaml')
assert state['phase']=='P5'
assert state['gates']['G5']['status']=='pending' and state['gates']['G5']['checks_passed']
assert all(state['gates'][g]['status']=='approved' for g in ['G1','G2','G3','G4'])
assert all(state['gates'][g]['status']=='invalidated' for g in ['G6','G7'])
execution=load(p/'ara/staging/P5-rerun-execution.json')
assert execution['jobs']==145
d=load(p/'results/diagnostics.json')
c=load(p/'results/channel-audit.json')
stamp=now()
git=['git','-c',f'safe.directory={repo.as_posix()}']
import json
historical=json.loads(subprocess.run(git+['show','74c87a8:implementation-state.json'],capture_output=True,check=True).stdout)
v=load(repo/'implementation-state.json')
v.update(updated_at=stamp,status='m11_g5_rerun_review_pending')
v['scientific_gates']={g:x['status'] for g,x in state['gates'].items()}
v['unresolved'][0]='M11 awaits fresh G5 PI approval, then independent P6 verification and P7 manuscript artifacts with PI gate decisions'
for key in ['m11_p5','m11_g5','m11_p6']:
    assert key+'_initial' not in v
    v[key+'_initial']=historical[key]
v['m11_p5']={
    'status':'R2 complete; fresh G5 PI review pending','code_revision':'R2','physical_protocol_version':'v1 unchanged',
    'protocol':'projects/m11-noma-qos/sim/protocol.yaml','protocol_commit':execution['protocol_commit'],
    'protocol_hash':execution['protocol_hash'],'planned_jobs':145,'completed_jobs':145,'resumed_jobs':0,
    'test_status':'PASS;123 combined framework/project checks','simulations':'PASS;145 fresh native manifest jobs',
    'protocol_locked':True,'scientific_approval':False,'gate_checks':'PASS',
    'review_packet':'projects/m11-noma-qos/to_human/G5-rerun-review.md',
    'gate_report':'projects/m11-noma-qos/to_human/G5-report.md',
    'scenario_evaluations':execution['scenario_evaluations'],'unique_channel_pairs':c['unique_blocks'],
    'source_changes':1,'relocks':1,'oracle_checks':d['oracle_checks'],
    'oracle_status_counts':d['oracle_status_counts'],'oracle_disagreements':len(d['disagreements']),
    'joint_unresolved_rows':execution['joint_unresolved_count'],
    'baseline_reproduction_agreement':True,'baseline_maximum_relative_error':execution['baseline_maximum_relative_error'],
    'independent_P6_verification':'NOT RUN; awaits renewed G5'}
v['m11_g5']={
    'status':'pending','checks_passed':True,'previous_approval_invalidated_by':'canonical PI rewind 76525a2',
    'timestamp':state['gates']['G5']['timestamp'],'review_packet':v['m11_p5']['review_packet']}
v['m11_p6']={
    'status':'awaits renewed G5 approval','gate_status':'invalidated','scientific_verification':'NOT RUN',
    'framework_entrypoint_repair':'applied/tested in P5 R2','independent_review_rounds':0,
    'engineering_review_independent':False,'engineering_findings':11,
    'supplement_brief':'projects/m11-noma-qos/ara/staging/P6-supplement-preparation.md'}
v['m11_p5_rerun'].update(status='complete; fresh G5 pending',new_runs_completed=145,
    resumed_jobs=0,output_files_byte_identical=1015,fresh_recomputation=True,
    execution_receipt='projects/m11-noma-qos/ara/staging/P5-rerun-execution.json')
save(repo/'implementation-state.json',v)
body=f'''
## Current P5 R2: fresh experiments complete; G5 pending

Following canonical PI rewind 76525a2, the committed code-only repair and fresh
lock produced all 145 planned native jobs with zero resumptions. All 1,015 saved
output files are byte-identical to archived R1, checked from actual old/new bytes
against both generations of manifests. Only lab/verification.py changes among
51 locked inputs. The physical v1 protocol and simulation sources remain unchanged.

All 123 combined tests and Ruff pass. Native collection, conditional statistics,
oracle diagnostics and seeded channel audit were freshly recomputed with their
ordinary integrity checks enabled. The fresh G5 request passes. G1-G4 remain
approved; G5 is pending; G6-G7 are invalidated. Earlier approval and repair-pending
sections above are historical and are preserved.

The finite-grid results retain five joint unresolved deterministic rows and
20 oracle-unresolved rows (four distinct stress cases repeated five times).
Resolved oracle disagreements are zero. Published OMA-subset maximum relative
error remains {100*execution['baseline_maximum_relative_error']:.4f}%.
No scientific P6 verifier has run. The author engineering audit identifies 11
coverage findings; its supplement brief does not substitute for independent
verification or an enforced artifact review. Review to_human/G5-rerun-review.md
and the newly generated G5-report.md. M11 remains in progress; M12 is unstarted.
'''
for name in ['findings.md','execution-plan.md']:
    f=p/name
    text=f.read_text(encoding='utf-8')
    assert '## Current P5 R2: fresh experiments complete; G5 pending' not in text
    f.write_text(text.rstrip()+'\n'+body,encoding='utf-8',newline='\n')
audit=repo/'docs/remaining-work-audit.md'
text=audit.read_text(encoding='utf-8')
start=text.index('## M11 work remaining')
end=text.index('## M12 work remaining',start)
replacement='''## M11 work remaining

Current status: G1–G4 approved. The canonical PI rewind to P5 invalidated the
first G5 approval and G6–G7. P5 R2 applies a tested verifier-entrypoint repair,
with the physical protocol unchanged, and completes 145 fresh native jobs.
All 123 combined tests pass. Actual output bytes match archived R1 and fresh
collection/statistics/channel/oracle summaries are regenerated. The new G5
request passes and awaits PI review in
`projects/m11-noma-qos/to_human/G5-rerun-review.md`.

After renewed G5 approval, P6 must execute the pinned verifier and independently
address the 11 coverage findings with analysis-only supplements, then obtain
enforced independent artifact review and a PI G6 decision. P7 still requires an
evidence-traced manuscript, verified citations, compilation, independent paper
review and PI G7 approval/report usability judgment. No P6 result or M11
completion is claimed. Earlier G1-pending preparation statements are historical.

'''
audit.write_text(text[:start]+replacement+text[end:],encoding='utf-8',newline='\n')
changelog=repo/'docs/CHANGELOG.md'
text=changelog.read_text(encoding='utf-8')
entry=f'''
## {stamp[:10]} — M11 P5 R2 verifier compatibility repair and rerun

- Verified the canonical PI rewind, preserving archived results and original
  G5 review evidence; fixed archived SVG byte transport with a scoped attribute.
- Accepted the verifier protocol alias, rejected conflicting declarations and
  preserved native integrity/independence guards; bounded verifier budget 3600s.
- Passed 123 combined tests and Ruff before relocking the code-only repair.
- Completed 145 fresh native jobs; 1,015 actual output files match archived R1.
  Recomputed collection, statistics, oracle diagnostics and seeded channel audit.
- Prepared a new passing G5 request and review packet. P6 coverage supplements
  remain preparation; scientific verification and independent review await G5.

'''
assert 'M11 P5 R2 verifier compatibility repair and rerun' not in text
first,rest=text.split('\n',1)
changelog.write_text(first+'\n'+entry+rest.lstrip('\n'),encoding='utf-8',newline='\n')
print({'status':v['status'],'G5':v['scientific_gates']['G5'],'completed_jobs':145})
