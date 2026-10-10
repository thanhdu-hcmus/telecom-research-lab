# M11 proposed scope — two-user NOMA with QoS

Status: AI-prepared draft. G1 and the synthetic profile require PI review.

## Purpose

Run the plan's established toy problem through P1–P7, with actual PI decisions
at G1–G7. Exercise handoffs, reports, evidence, verification and manuscript
export. This benchmark makes no novelty claim and selects no dissertation topic.
The scoped profile is `profile.yaml`; the real thesis profile is separate.

## Proposed comparison

- Single-antenna downlink, two scalar users ordered by channel power gain.
- Perfect instantaneous CSI, ideal SIC, unit normalized noise and bandwidth.
- Both schemes share each channel realization and the same total transmit
  power. Report spectral efficiency in bit/s/Hz; declare all SNR conversions.
- OMA allocates equal time to each user, with the same instantaneous total
  transmit power while active. State this scheduler in every comparison.
- NOMA chooses its power split to maximize sum rate subject to the same
  per-block QoS constraints. The weak user's minimum feasible allocation and
  strong user's maximum feasible allocation define the admissible interval.
- Identify infeasible realizations explicitly. Compare sum rates where OMA and
  NOMA are both feasible; separately report feasibility fractions and paired
  sample counts. Never discard infeasible cases without reporting them.

The proposed acceptance case is the ideal degraded broadcast channel with a
matched equal-time OMA reference and feasible QoS. The later P4 derivation must
establish the conditions supporting NOMA ≥ OMA; P6 must check them independently.
This is a conditional benchmark expectation, not a universal measured result.
Exact channel distributions, QoS values, SNR grids, stopping criteria and seeds
remain proposals until their respective model and protocol gates.

## Boundaries

CPU-scale work only. Exclude RIS and mmWave propagation, mobility, learning,
imperfect CSI and residual SIC from this benchmark. These can be considered in
later research with their own approved scope. Use legitimate full papers and
grounded cards; keep established-method novelty verdicts truthful.

## Acceptance and review

All seven gates must pass through the CLI with actual PI decisions; all artifacts
must validate; the bounded qualitative comparison must be supported; the paper
must compile. The PI must rate every gate report usable, with issues corrected.
Each later phase stops at its gate. No literature phase or simulation has begun.

## Provenance

Problem and acceptance requirements: `Telecom-Research-Lab-Plan.md`, M11.
Comparison safeguards: `docs/plan-review.md`, R13. Assumptions above are AI
proposals awaiting review; no PI scientific decision or original result is inferred.
