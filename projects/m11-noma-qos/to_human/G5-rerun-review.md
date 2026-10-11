# G5 review — P5 R2 rerun

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
  **1015 output files are byte-identical**.
  Environment and job parameters also match. Run IDs, source commits, timestamps
  and runtime receipts change; manifests are not claimed byte-identical.
- Collection, statistics, oracle diagnostics and seeded channel audit were
  recomputed from fresh outputs using the original programs with all native
  integrity checks enabled. Original summaries were not substituted.
- Fresh numerical fields in statistics, oracle diagnostics, channel audit and
  native collection match R1. Only declared lineage and measured runtime fields
  are excluded from that comparison; new bindings are checked separately.
- Protocol commit: `b2a7cf17890b499b07f5c23bbc871351cc3909b1`.
  Physical protocol SHA256: `250ccb4ad29282be0cb2f02a7eb5bda4cb64b6adf4dbd11d4f00949bf6320e51`.
- Total job runtime: **1638.9 seconds**, including runner
  completion checks. Raw CSV: **3.548 GB** per generation,
  retained locally and bound by manifests. Raw CSV/PDF/binary stores are not
  committed to Git.

## Conditional rates and feasibility

The run contains **4,718,592 Monte Carlo scenario evaluations plus 100
deterministic rows** (20 cases repeated five times). There are
**393,216 unique channel pairs**, reused across the grid.
Grid reuse and deterministic repeats do not create independent replicates.
Saved PCG64 draws reproduce exactly and satisfy common-channel checks.

Rates are bit/s/Hz. Each MC setting contains 393,216 evaluations. n00 means
neither scheme feasible; n10 means NOMA only; n11 means both feasible.
The complete ledger retains n01 and unresolved cases. OMA-only count: **0**;
negative paired differences beyond 1e-9: **0**; candidate rate/SIC violations:
**0** in this finite sample. Joint unresolved count including deterministic
checks: **5**.

Mean gain and 95% Student-t intervals use n11 only. Pointwise intervals do not
establish familywise coverage across the grid. All conditional rate intervals
meet the declared 1% relative halfwidth target. Positive-QoS outage event counts
for NOMA/OMA infeasibility meet the protocol minimum; zero events give a positive upper confidence bound,
not proof of probability zero. Structural zero-QoS statements are separate.

| P (dB) | (qw, qs) | n00 | n10 | n11 | Mean NOMA−OMA [95% CI] | Relative CI halfwidth |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| 0 | (0, 0) | 0 | 0 | 393216 | 0.3386 [0.3378, 0.3394] | 0.242% |
| 0 | (0.25, 0.25) | 162073 | 60147 | 170996 | 0.1566 [0.1559, 0.1572] | 0.425% |
| 0 | (0.5, 0.5) | 296661 | 43515 | 53040 | 0.1082 [0.1073, 0.1091] | 0.795% |
| 10 | (0, 0) | 0 | 0 | 393216 | 0.7517 [0.7499, 0.7534] | 0.228% |
| 10 | (0.25, 0.25) | 15788 | 15260 | 362168 | 0.6170 [0.6155, 0.6184] | 0.231% |
| 10 | (0.5, 0.5) | 36824 | 34480 | 321912 | 0.5270 [0.5257, 0.5283] | 0.249% |
| 20 | (0, 0) | 0 | 0 | 393216 | 0.9460 [0.9437, 0.9484] | 0.246% |
| 20 | (0.25, 0.25) | 1466 | 1738 | 390012 | 0.9104 [0.9082, 0.9126] | 0.240% |
| 20 | (0.5, 0.5) | 3329 | 4422 | 385465 | 0.8768 [0.8747, 0.8789] | 0.236% |
| 30 | (0, 0) | 0 | 0 | 393216 | 0.9909 [0.9883, 0.9934] | 0.259% |
| 40 | (0, 0) | 0 | 0 | 393216 | 0.9982 [0.9956, 1.0008] | 0.263% |
| 50 | (0, 0) | 0 | 0 | 393216 | 0.9992 [0.9966, 1.0018] | 0.263% |

## Oracle diagnostics and numerical limits

The distinct original-SINR scalar oracle checked **4708**
preselected rows: `{'feasible': 4129, 'infeasible': 559, 'unresolved': 20}`. Tighter-tolerance counts:
`{'feasible': 1012, 'infeasible': 148}`. Resolved feasibility/objective disagreements:
**0**. Maximum resolved objective difference:
**6.66755539668884e-12**. Maximum tighter-tolerance objective
difference: **4.2730263771773025e-12**.

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
versus equation difference: **0.1716%** (required ≤5%). Trend and
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
.\.venv\Scripts\lab.exe gate approve G5 --project m11-noma-qos --note "P5 R2 rerun and numerical limits reviewed; G5 report usable" --json
```

Enter the fresh CLI confirmation yourself and use your actual usability judgment
in the note. If revisions are needed, use gate revise with an explanatory note.
The lab-orchestrator skill requires the PI G5 decision before P6 starts.
