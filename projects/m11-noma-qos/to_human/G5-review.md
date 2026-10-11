# G5 review — M11 simulations

## Decision requested

Review the completed P5 runs and numerical limitations. G1-G4 are approved;
G5 is a separate PI decision. The model is an established ideal scalar benchmark,
with no novelty, publication-readiness or practical deployment claim. Independent
P6 results verification and manuscript work have not started.

## Completed work

- 145 planned manifest jobs completed under the unchanged v1 protocol and code.
- 4,718,592 Monte Carlo scenario evaluations plus 100 deterministic rows (20 cases
  repeated five times). There are 393,216 unique channel pairs, reused
  across the grid; grid evaluations and deterministic repeats are not independent replicates.
- 31 targeted simulation/physics checks and 90 framework regression checks passed.
- The first regression attempt had 41 temporary-folder setup errors; a fresh
  verified workspace temporary folder fixed execution without changing source.
  The failed attempt and original test-request rejection remain in provenance.
- All 51 locked inputs remain bound to Git commit
  `ebb68ac514beeb89d5d1e3dfcb20aecdeaf440ca`. Protocol hash: `250ccb4ad29282be0cb2f02a7eb5bda4cb64b6adf4dbd11d4f00949bf6320e51`.
- Original seeded draws reproduce exactly, shared gains match across all 144
  Monte Carlo jobs, and ordered gain means pass the declared finite sanity check.
- Measured sum of job runtimes: 960.8 seconds. Raw CSV:
  3.548 GB, retained locally and checksum-bound in manifests.
  Raw CSV/PDF/binary stores are not committed to Git.

## Feasibility and conditional rate gains

Rates are bit/s/Hz. Every MC setting has 393,216 evaluations. n00 means neither
scheme feasible, n10 NOMA only, n11 both feasible. The full machine-readable
ledger includes n01 and unresolved counts. Total OMA-only count: **0**;
paired negative-difference count beyond 1e-9: **0**. Total unresolved
joint classifications across all settings/cases: **5**.

Gain and 95% Student-t CI use n11 only. The denominator is never the full count
when conditioning on feasibility. Pointwise intervals do not give familywise
coverage across this grid. Zero observed outage events yield positive confidence upper bounds; they do
not prove probability zero. The zero-QoS model statement is recorded separately.

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

Settings failing the <=1% conditional rate-CI target: **none**.
This is numerical consistency with the G4 prediction in these sampled regimes,
not an independent P6 validation or universal finite-precision proof.

## Distinct scalar oracle and boundaries

The distinct original-SINR oracle checked 4708 preselected rows;
status counts: `{'feasible': 4129, 'infeasible': 559, 'unresolved': 20}`. Tighter-tolerance status counts:
`{'feasible': 1012, 'infeasible': 148}`. Resolved feasibility/objective disagreements:
**0**. Maximum resolved objective difference:
**6.66755539668884e-12**. Maximum tighter-tolerance objective
difference: **4.2730263771773025e-12**.

Unresolved oracle reasons: `{'Exact feasible witness found, maximum unresolved in narrow interval': 5, 'Narrow/singleton domain without an exact direct certificate': 10, 'Numerical concavity objective gap exceeds tolerance': 5}`. Every unresolved row,
original input, attempted certificate and reason remains in diagnostics.json
and its raw oracle.json. The 20 unresolved oracle rows are five repeats of
four distinct cases: A=3, B=9±1e-12 at (qw, qs)=(1,2); A=1e100, B=2e100
at (1,1); and A=B=1 at (0.5,0.5). The last case supplies the five joint
unresolved rows. None of these repeats is an independent statistical draw.
Exact rational singleton feasibility and approximate
logarithmic rates are distinguished. The numerical secant objective envelope
uses the approved concavity law and is **not** a rigorous interval-arithmetic
certificate of arbitrary real-input optimality. A missed grid point never proves
infeasibility. Allocation-grid/fixed-split losses are algorithm diagnostics.

## OMA reference reproduction

The two OMA curves from Fair-NOMA Figure 1 (PDF page 4), beta=1, are reproduced
at 0/10/20/30/40/50 dB using the paper's exact equations (6)-(8) on page 3.
Maximum relative MC-versus-equation difference: **0.1716%**
(required <=5%). Agreement: **True**;
strong-versus-weak ordering and increasing-SNR trends are checked.
See the [overlay](../results/oma-reference-overlay.svg).

This covers the OMA subset of the figure, not the Fair-NOMA allocation curves
or every paper figure. No third-party software package is accepted or executed,
no paper-specific half-power restriction is imported, and discovery records
remain unchanged. The protocol's incorrect root-LICENSE reference is corrected
in [the documentary erratum](../sim/protocol-errata.md); no license points or
repository-wide license are claimed. Numerical settings and input bytes are unchanged.

## Evidence and limits

The generic collection summary.csv averages raw metrics and retains NaN for
undefined rates. Use statistics.json for the conditional scientific estimates
and complete feasibility ledger. Positive-QoS outage event counts exceed the
protocol minimum for NOMA/OMA infeasibility; zero OMA-only events and zero-QoS
infeasibility are reported with confidence upper bounds and separate model statements.

- [Locked protocol](../sim/protocol.md) and [lock](../sim/lock.json).
- [Statistics](../results/statistics.json), [oracle diagnostics](../results/diagnostics.json),
  [channel audit](../results/channel-audit.json), and results/runs/*/manifest.json.
- [Initial test evidence](../../../docs/evidence/m11-p5-tests-initial.json) and
  [successful regression rerun](../../../docs/evidence/m11-p5-regression.json).
- [Generated gate report](G5-report.md) binds all phase artifacts, including local raw data.
- ara/trace/sessions records actual authorization, preparation, tests and experiments.

Perfect CSI, ideal SIC, Shannon rates, scalar ordering and equal-time OMA remain
the approved assumptions. There is no imperfect-CSI/SIC, finite-block, modulation,
hardware, geometry or optimized-OMA evidence. The QoS/SNR grid is finite; asymmetric
and zero/equal/singleton cases are deterministic checks, not a complete real-domain
implementation guarantee. The prepared P6 verifier has not been independently
reviewed or run. M11 remains in progress; M12 remains unstarted.

## PI action

After reviewing this packet and confirming that the generated G5 report passes,
run from the repository root:

```powershell
.\.venv\Scripts\lab.exe gate approve G5 --project m11-noma-qos --note "P5 runs and numerical limits reviewed; G5 report usable" --json
```

Enter the fresh CLI confirmation yourself. Use your actual usability judgment
in the note. If revisions are needed, use gate revise with an explanatory note.
The lab-orchestrator skill requires the PI G5 decision before P6 starts.
