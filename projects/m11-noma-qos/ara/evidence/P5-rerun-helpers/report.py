"""Prepare the fresh G5 review packet, preserving the original packet and receipts."""
from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from lab.io import load, save, now, sha256

repo = Path.cwd()
p = repo/'projects/m11-noma-qos'
subprocess.run([sys.executable,str(repo/'.cache/p5_rerun_compare_derived.py')],cwd=repo,check=True)
s = load(p/'results/statistics.json')
d = load(p/'results/diagnostics.json')
c = load(p/'results/channel-audit.json')
l = load(p/'sim/lock.json')
comparison = load(p/'ara/staging/P5-rerun-output-comparison.json')
recomputed = load(p/'ara/staging/P5-rerun-recomputation.json')
prep = load(p/'ara/staging/P5-rerun-preparation.json')
assert comparison['status'] == recomputed['status'] == c['status'] == 'PASS'
assert d['jobs'] == 145 and not d['disagreements']
assert s['baseline_reproduction']['agreement']
precision = [x['scenario'] for x in s['scenarios'] if x['params']['kind'] != 'deterministic' and not all(x['rate_precision'].values())]
assert not precision, precision
assert all(x['counts']['n01'] == x['negative_paired_count'] == x['candidate_violation_count'] == 0 for x in s['scenarios'])
positive_qos_event_checks = []
for scenario in s['scenarios']:
    if scenario['params']['kind'] == 'deterministic' or not (scenario['params']['qw'] or scenario['params']['qs']):
        continue
    for metric in ['noma_infeasibility','oma_infeasibility']:
        event = scenario['event_statistics'][metric]
        assert event['events'] >= 100 and event['conclusive'], (scenario['scenario'],metric,event)
        positive_qos_event_checks.append({'scenario':scenario['scenario'],'metric':metric,'events':event['events'],'minimum_events':100,'passed':True})
root = ET.parse(repo/'.cache/m11-p5-rerun-tests.xml').getroot()
suites = [root] if root.tag == 'testsuite' else list(root.findall('testsuite'))
tests = sum(int(x.attrib['tests']) for x in suites)
assert tests == 123
assert all(int(x.attrib.get(k,0)) == 0 for x in suites for k in ['failures','errors','skipped'])
max_error = max(v for x in s['baseline_reproduction']['points'] for v in x['relative_error'].values())
total = sum(x['N_total'] for x in s['scenarios'])
unresolved = sum(x['counts']['unresolved'] for x in s['scenarios'])
rows = []
for x in s['scenarios']:
    if x['params']['kind'] == 'deterministic':
        continue
    q, counts, stat = x['params'], x['counts'], x['paired_statistics']['paired_difference']
    gain = 'undefined' if stat is None else f"{stat['mean']:.4f} [{stat['low']:.4f}, {stat['high']:.4f}]"
    half = 'undefined' if stat is None else f"{100*stat['relative_halfwidth']:.3f}%"
    rows.append(f"| {q['P_db']} | ({q['qw']}, {q['qs']}) | {counts['n00']} | {counts['n10']} | {counts['n11']} | {gain} | {half} |")
text = f'''# G5 review — P5 R2 rerun

## Decision requested

Review the fresh P5 results after the canonical PI rewind. G1–G4 remain
approved. G5 requires a new PI decision; the earlier G5 approval was invalidated
by the rewind. This is an established ideal scalar benchmark, with no novelty,
publication readiness or practical deployment claim. Independent P6 verification
has not run.

## Repair and reproducibility

- PI rewind commit `76525a2` archived the original P5 inputs and results.
- Only `lab/verification.py` changed among the 51 locked inputs. It accepts the
  protocol's `verifier` alias, rejects conflicting declarations and retains
  pinning and independence guards. Its bounded verifier budget is 3600 seconds.
  No actual P6 timeout or measured P6 budget adequacy is claimed.
- The physical v1 protocol, simulation sources, model, scenarios, metrics,
  tolerances and baselines are unchanged. R2 is a code revision.
- All **123** combined framework/project tests passed with no errors, failures
  or skips; Ruff passed. Earlier failed trials remain in provenance.
- Fresh native runs completed **145 jobs**, with **zero resumed jobs**.
  Actual archived and fresh bytes were read and checked against both manifests:
  **{comparison['output_files_compared']} output files are byte-identical**.
  Environment and job parameters also match. Run IDs, source commits, timestamps
  and runtime receipts change; manifests are not claimed byte-identical.
- Collection, statistics, oracle diagnostics and seeded channel audit were
  recomputed from fresh outputs using the original programs with all native
  integrity checks enabled. Original summaries were not substituted.
- Fresh numerical fields in statistics, oracle diagnostics, channel audit and
  native collection match R1. Only declared lineage and measured runtime fields
  are excluded from that comparison; new bindings are checked separately.
- Protocol commit: `{l['protocol_commit']}`.
  Physical protocol SHA256: `{l['protocol_hash']}`.
- Total job runtime: **{d['total_job_runtime_s']:.1f} seconds**, including runner
  completion checks. Raw CSV: **{d['raw_csv_bytes']/1e9:.3f} GB** per generation,
  retained locally and bound by manifests. Raw CSV/PDF/binary stores are not
  committed to Git.

## Conditional rates and feasibility

The run contains **4,718,592 Monte Carlo scenario evaluations plus 100
deterministic rows** (20 cases repeated five times). There are
**{c['unique_blocks']:,} unique channel pairs**, reused across the grid.
Grid reuse and deterministic repeats do not create independent replicates.
Saved PCG64 draws reproduce exactly and satisfy common-channel checks.

Rates are bit/s/Hz. Each MC setting contains 393,216 evaluations. n00 means
neither scheme feasible; n10 means NOMA only; n11 means both feasible.
The complete ledger retains n01 and unresolved cases. OMA-only count: **0**;
negative paired differences beyond 1e-9: **0**; candidate rate/SIC violations:
**0** in this finite sample. Joint unresolved count including deterministic
checks: **{unresolved}**.

Mean gain and 95% Student-t intervals use n11 only. Pointwise intervals do not
establish familywise coverage across the grid. All conditional rate intervals
meet the declared 1% relative halfwidth target. Positive-QoS outage event counts
for NOMA/OMA infeasibility meet the protocol minimum; zero events give a positive upper confidence bound,
not proof of probability zero. Structural zero-QoS statements are separate.

| P (dB) | (qw, qs) | n00 | n10 | n11 | Mean NOMA−OMA [95% CI] | Relative CI halfwidth |
| --- | --- | ---: | ---: | ---: | --- | ---: |
{chr(10).join(rows)}

## Oracle diagnostics and numerical limits

The distinct original-SINR scalar oracle checked **{d['oracle_checks']}**
preselected rows: `{d['oracle_status_counts']}`. Tighter-tolerance counts:
`{d['tighter_status_counts']}`. Resolved feasibility/objective disagreements:
**{len(d['disagreements'])}**. Maximum resolved objective difference:
**{d['maximum_objective_agreement_error']}**. Maximum tighter-tolerance objective
difference: **{d['maximum_tighter_objective_difference']}**.

The 20 unresolved oracle rows are five repeats of four distinct stress cases:
A=3, B=9±1e-12 at (qw, qs)=(1,2); A=1e100, B=2e100 at (1,1); and A=B=1
at (0.5,0.5). The last case supplies the five joint unresolved rows. All inputs,
attempted certificates and reasons remain in diagnostics and raw oracle files.
Unresolved results are retained. Exact rational singleton feasibility is
distinguished from approximate logarithmic rates. The numerical secant gap
is not a rigorous interval-arithmetic certificate. A missed allocation-grid
point does not prove infeasibility.

## OMA reference reproduction

The OMA subset of Fair-NOMA Figure 1 (PDF page 4), beta=1, is reproduced at
0/10/20/30/40/50 dB using equations (6)–(8) on page 3. Maximum relative MC
versus equation difference: **{100*max_error:.4f}%** (required ≤5%). Trend and
strong/weak ordering checks pass. See the [overlay](../results/oma-reference-overlay.svg).
This does not reproduce Fair-NOMA allocation curves or every paper figure.
No third-party software baseline is accepted or executed. The documentary
[LICENSE-reference erratum](../sim/protocol-errata.md) remains unchanged;
no repository-wide license or license points are claimed.

## P6 preparation and remaining work

The engineering audit records 11 findings about verifier coverage. It is an
author engineering review, not an independent scientific verdict. The prepared
[supplement brief](../ara/staging/P6-supplement-preparation.md) covers independent
raw-rate/SIC checks, feasibility/ledger reconstruction, metrics alignment,
ablations, CI/event policy, seeded sampling and shared-reference replay.
Actual P6 implementation/execution follows fresh G5 approval. A separate
enforced independent artifact review remains required. Native verifier runtime
and memory adequacy are unmeasured. No P6 acceptance is inferred from P5 PASS.

Perfect CSI, ideal SIC, Shannon rates, scalar ordering and equal-time OMA remain
the assumptions. There is no imperfect CSI/SIC, hardware, finite-block,
modulation, geometry or optimized-OMA evidence. M11 remains in progress;
M12 remains unstarted.

## Evidence

- [Protocol](../sim/protocol.md), [fresh lock](../sim/lock.json), and results/runs/*/manifest.json.
- [Statistics](../results/statistics.json), [oracle diagnostics](../results/diagnostics.json),
  [channel audit](../results/channel-audit.json), [native collection](../results/collection.json).
  Generic summary.csv retains NaN for undefined rates; use statistics.json for
  conditional scientific estimates and complete ledgers.
- [R2 preparation and tests](../ara/staging/P5-rerun-preparation.json),
  [actual-byte comparison](../ara/staging/P5-rerun-output-comparison.json),
  [derived-field comparison](../ara/staging/P5-rerun-derived-comparison.json),
  [fresh recomputation receipt](../ara/staging/P5-rerun-recomputation.json).
- [Engineering audit](../ara/staging/P5-rerun-engineering-review.json).
- [Generated current G5 report](G5-report.md) binds phase artifacts including
  local raw data. Original review/receipts and archive evidence are preserved.
- ara/trace/sessions records actual PI authorization, tests, failed trials,
  source repair, lock and fresh experiments.

## PI action

After reviewing this packet and checking that the generated G5 report passes,
run from the repository root:

```powershell
.\\.venv\\Scripts\\lab.exe gate approve G5 --project m11-noma-qos --note "P5 R2 rerun and numerical limits reviewed; G5 report usable" --json
```

Enter the fresh CLI confirmation yourself and use your actual usability judgment
in the note. If revisions are needed, use gate revise with an explanatory note.
The lab-orchestrator skill requires the PI G5 decision before P6 starts.
'''
packet = p/'to_human/G5-rerun-review.md'
assert not packet.exists(), 'Preserve an already prepared review packet'
packet.write_text(text,encoding='utf-8',newline='\n')
save(p/'ara/staging/P5-rerun-execution.json', {
    'timestamp':now(), 'status':'fresh P5 results complete; fresh G5 request next',
    'code_revision':'R2', 'physical_protocol_version':'v1 unchanged',
    'protocol_commit':l['protocol_commit'], 'protocol_hash':l['protocol_hash'],
    'jobs':145, 'resumed_jobs':0, 'scenario_evaluations':total,
    'unique_channel_pairs':c['unique_blocks'], 'combined_tests':tests,
    'changed_locked_inputs':['lab/verification.py'], 'relocks':1,
    'oracle_status_counts':d['oracle_status_counts'], 'oracle_disagreements':len(d['disagreements']),
    'joint_unresolved_count':unresolved, 'rate_precision_failure_settings':precision,
    'positive_qos_outage_event_checks':positive_qos_event_checks,
    'baseline_maximum_relative_error':max_error, 'fresh_raw_output_recomputation':True,
    'independent_P6_verification':'NOT RUN', 'engineering_audit_independent':False,
    'evidence':{name:sha256(p/name) for name in [
        'sim/lock.json','results/statistics.json','results/diagnostics.json','results/channel-audit.json',
        'results/collection.json','results/summary.csv','results/oma-reference-overlay.svg',
        'ara/staging/P5-rerun-output-comparison.json','ara/staging/P5-rerun-recomputation.json',
        'ara/staging/P5-rerun-derived-comparison.json',
        'ara/staging/P5-rerun-preparation.json','ara/staging/P5-rerun-engineering-review.json',
        'ara/staging/P6-supplement-preparation.md','to_human/G5-rerun-review.md']}})
old_report = p/'to_human/G5-report.md'
preserved = p/'ara/evidence/G5-original-report.md'
assert not preserved.exists()
preserved.write_bytes(old_report.read_bytes())
assert sha256(preserved) == sha256(old_report)
print({'report':str(packet), 'tests':tests, 'evaluations':total, 'baseline_max_relative_error':max_error})
