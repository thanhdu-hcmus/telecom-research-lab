# M11 numerical protocol v1

## Authorization and purpose

G4 was approved by the PI in commit 08808d8. P5 phase start passed. This is
the established, ideal scalar benchmark selected at G3, not a novelty claim.
No data have been sampled under this protocol at authoring time. Commit every
input before `lab sim lock`; run only through `lab sim run`. G5 reviews completed
experiments; P6 independently verifies results after actual G5 approval.

## Physical model and comparison

All seven G4 assumptions and predictions apply unchanged. Total normalized
power P equals linear received SNR for a unit channel gain and unit noise.
Generate two independent unit-mean exponential power gains, sort each pair
weak/strong, and reuse identical draws for all methods and diagnostics. This
is an explicit sampling choice within the approved ideal scalar model, with no
geographic path loss, antenna, estimation or coding model. Perfect CSI and ideal
SIC; bandwidth and block length normalized to one. NOMA uses the whole block
and a strong-user fraction a in [0,1]. OMA uses full P during each half-block.
Both expend energy P per block and use the same gains and per-user fixed QoS.
P is a normalized ratio, not watts or dBm. Rates are bit/s/Hz per full block.
Use the framework's dB-to-linear helper only for scenario conversion.

## Scenarios and fixed workload

Primary grid: P in {0,10,20} dB, fixed (qw,qs) in {(0,0),(.25,.25),(.5,.5)}.
Reference-only extension: (0,0) at {30,40,50} dB. Twelve MC scenarios total.
Each has seeds 11001 through 11012 and 32,768 trials per seed: 393,216 blocks
per setting. PCG64 with SeedSequence([seed,0]) supplies channels. Reusing each
seed's ordered gains across the grid is deliberate; seed streams are independent
within a scenario. No seed selection, adaptive stopping or post-result extension.
No random noise or optimizer initialization is needed for these Shannon rates.
Fixed N is a CPU-scale planning choice aiming for <=1% relative 95% CI halfwidth;
it is not a guarantee. Report any failed precision/event threshold as inconclusive.

Deterministic cases (one manifest job, 100 rows: repeat the fixed 20-case table
five times) cover zero power, zero gains, zero targets, positive targets at zero
gain, equal-gain ties, exact singleton at A=3,B=9,qw=1,qs=2, equal-gain singleton,
weak-only and strong-only QoS, clearly infeasible QoS, narrow positive/empty
intervals, tiny SNR, huge but finite SNR, and asymmetric targets. Repeated rows
are not independent samples and receive no statistical CIs. The cases are
committed in cases.yaml; no data-dependent cases are added to this run.

## Implementation, numerical uncertainty and oracle

analytic.py evaluates the approved closed form with log1p/expm1 and explicit
zero branches. Infeasible optima are undefined (NaN in raw CSV, null in JSON).
Target values, gains and P must be finite and nonnegative and gains ordered.
Binary64 intermediate overflow or unresolved near-boundary comparisons are
flagged. A tolerance cannot create mathematical feasibility or clamp an empty
interval. Integer-target ambiguous cases may use an exact rational certificate
for the binary64 inputs; noninteger ambiguous cases remain unresolved.
Record N_total, N_resolved, N_unresolved and all four joint feasibility counts.
The exact four-count identity applies to N_resolved; unresolved blocks are
preserved separately and make any unqualified full-ensemble conclusion invalid.

oracle.py is a distinct implementation: no analytic imports or copied endpoint
decision. It uses original SINRs over [0,1] and bracketed original constraints,
then a bounded objective search. Integer-target rational certificates and
conservative objective bounds, when available, are distinguished from numerical
solver agreement. Failure to settle a singleton/narrow interval is unresolved,
never infeasible merely because a grid missed it. Run it for all 100 deterministic
rows and the first 32 MC rows of every seed, without outcome-based selection.
Rerun the first eight of those rows with tolerances ten times tighter; save both.
Proposed rate tolerance 1e-9, split tolerance 1e-12, objective tolerance 1e-7;
root cap96 per constraint and bounded optimizer cap256 iterations; record actual
solver caps/statuses. These qualify numerical agreement only.
Full oracle implementation details and guaranteed domain are in the engineer
design artifact; any limits must be reported in G5, not hidden by a PASS badge.

## Metrics, denominators and diagnostics

Record original gains, targets, P, analytic candidate/split, interval bounds,
original SINRs, both weak decoding rates, strong rate, OMA individual rates,
feasibility statuses and residuals. n00: neither feasible; n01: OMA only;
n10: NOMA only; n11: both feasible. Counts must reconstruct every resolved row.
Feasibility estimates use the full resolved count, with unresolved count adjacent.
Report individual infeasibility counts as well as joint infeasibility.
Optimal NOMA sum, matched OMA sum and their paired difference are summarized
only on n11. Retain all infeasible rows; no undefined optimum becomes zero.
If n11=0 the paired mean/CI is undefined. No individual-rate dominance claim.

P1-P7 diagnostics: SIC dominance, interval membership/classification, objective
agreement, target activation, OMA-only count, paired negative-difference count,
ledger reconstruction and oracle disagreements/unresolved statuses. These are
numerical validation receipts, not finite-sample proofs of universal laws.
Two algorithm ablations use these same channels/QoS/resources: fixed a=.25 and
101-point exhaustive grid including endpoints. Record their feasibility and
objective loss relative to analytic optimum only when both allocations are
feasible. A grid miss is not a certified infeasible case. These are diagnostics
of allocation/search, not newly selected literature baselines or objectives.

## Statistical policy

Compute the paired rate mean from all both-feasible independent blocks in a
setting; conditional sampling produces independent draws from the conditional
distribution. Use a two-sided 95% Student-t CI on those paired differences and
on the two conditional sum means, n=n11 (not total draws). n<2 => undefined CI.
Cross-setting draws are paired and no cross-setting significance claims are made.
For feasibility/infeasibility counts use two-sided 95% exact binomial intervals.
At least 100 observed infeasibility events are needed for a conclusive outage
estimate. Zero events yield an upper bound, not a zero outage proof. For an
identically feasible zero-QoS analytic regime, report the mathematical reason
separately from the empirical bound. Confidence intervals are pointwise; no
familywise guarantee across the grid. Deterministic ties and zero means receive
absolute residuals, not a meaningless relative halfwidth criterion.

## OMA baseline reproduction

The selected baseline is the already approved matched equal-time OMA. Implement
it locally from Fair-NOMA (Oviedo/Sadjadpour, TVT 2017), source PDF page2,
Section III; page3 equations (6)-(8); Figure1 on page4 with beta=1. Reproduce
only its two OMA curves on {0,10,20,30,40,50} dB, using all unfiltered draws from
zero-QoS scenarios. Reference values are evaluated from the paper's exact
published equations, not invented/digitized plot coordinates:

- E[RwO] = exp(2/P) E1(2/P)/(2 ln2).
- E[RsO] = [2 exp(1/P) E1(1/P) - exp(2/P) E1(2/P)]/(2 ln2).
- E[SO] = exp(1/P) E1(1/P)/ln2.

Require <=5% relative difference, correct strong>weak ordering, both curves
increasing with P, and report observed CIs. An overlay compares MC estimates to
these exact reference curves. This is reproduction of the OMA subset of Figure1,
not the paper's channel-dependent Fair-NOMA allocation or every curve/figure.
No external code package is accepted or executed, no paper-specific half-power
constraint is imported, no publisher figure image is redistributed. Generated
synthetic data need no external dataset. Local source/dependencies are reviewed;
the framework LICENSE governs original implementation, not ownership of papers.

## Evidence and execution

Language: Python in the existing uv.lock-pinned environment; no learning/MATLAB
route required for this scalar run. Budget estimate: <=1 GB per job, 145 serial
jobs, seconds to minutes per job; runtime is measured, not promised. All input
code, fixed cases, protocol, uv.lock, framework Python/MATLAB code are locked.
Raw CSV is local and git-ignored, accessible through checksum-bound manifests.
Commit summaries, manifests, collection receipt, protocol and review artifacts.
No raw binary stores or PDFs are committed. Keep failed jobs/logs and retain
old runs if a code fix forces relock. Resume only verified complete jobs.
The raw collector is a checksum/inventory convenience: its unconditioned means
and NaNs are not the scientific summary; aggregate.py implements the declared
denominators. P6 will independently recompute before manuscript claims.

Before locking, run the unit/physics checks explicitly required by the user's
implementation plan, section5.5. Then commit inputs, lock, run/status/collect,
aggregate and reproduce the reference overlay. Request G5 with full limitations
and provenance. Do not enter P6 or approve G5 for the PI.
