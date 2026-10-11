# G3 review: M11 benchmark option

## Decision requested

Select one eligible option for the approved two-user scalar NOMA/QoS versus
matched equal-time OMA dry run. Recommendation: **idea-01**, the analytic feasible
interval and endpoint optimizer with an independently written scalar oracle.
It gives a compact, inspectable starting point for model and implementation checks.
The selection remains yours; no option has been selected and G3 is not approved.

The `lab-orchestrator` skill and repository AGENTS.md require a PI selection at G3
before P4 modelling. Your “Okie, approved” authorized the external audit; that
approval is recorded in provenance session `2026-10-11-0007`.

## What is ready

- 15 schema-valid cards, each with three included full-paper closest works.
- 15 independent reports, each supported by five distinct card-specific executed
  searches across scholarly and author/code discovery.
- 82 independent search receipts representing 81 distinct strings. Two original
  receipts had display/mapping limitations and were excluded from the five-per-card
  minimum; replacements/reruns are retained. Five shared context queries are separate.
- All 15 verdicts are `already-done` for established scientific methods and benchmark
  adaptation. This does not assert one published identical complete validation suite.
- Ranking and sensitivity regenerated from current cards and the existing policy.
- Parent validation passed; actual named reviewer runtime was read-only and its
  supplied packet was unchanged. The first two unsuccessful attempts are retained.

There are no model derivations, simulations or measured M11 results at this gate.
The approved scope/profile/literature/baseline candidates remain unchanged.

## Shortlist

| Option | Emphasis | Score | Planning risk |
| --- | --- | --- | --- |
| idea-01 | Analytic QoS interval and optimal endpoint, checked by an independent scalar oracle | 42/50 | 1/5 |
| idea-07 | Paired feasibility ledger and explicit denominators for conditional rate comparisons | 42/50 | 1/5 |
| idea-02 | Exhaustive split evaluation with narrow-interval and discretization checks | 42/50 | 2/5 |

Every option covers the same approved core comparison. These are alternative
validation emphases. Final distributions, QoS/SNR grids, seeds, sample counts,
stopping rules and tolerances remain P4/P5 proposals for their later gates.

## Ranking interpretation

Configured weights are fit 5, time 3, venue 2. Ten cards tie at 42/50 and five at
37/50. All time scores are 5 because AI planning estimates fall within three
months; all venue scores are 1 because the target is internal M11 acceptance.
Scores separate synthetic-benchmark fit, then risk and ID tie breakers.
Idea-01 precedes idea-07 by the configured ID tie breaker; the score alone does
not establish scientific superiority. Planning risks and budgets are estimates.

The top three are unchanged in all seven tested weight combinations (the base
case plus six one-point changes preserving total ten). This stability partly
reflects the flat time/venue scores and coarse fit/risk ordering. It is not a
claim about all possible weights, novelty, publication suitability or future results.

## All eligible options

| Rank | ID | Option | Score | Planning risk |
| --- | --- | --- | --- | --- |
| 1 | idea-01 | Analytic feasible-interval optimizer with an independent scalar oracle | 42/50 | 1 |
| 2 | idea-07 | Paired feasibility ledger for conditional rate comparisons | 42/50 | 1 |
| 3 | idea-02 | Bounded exhaustive allocation checks with discretization accounting | 42/50 | 2 |
| 4 | idea-04 | Rate-region construction of a matched OMA comparison witness | 42/50 | 2 |
| 5 | idea-05 | Weak-message decoding consistency at both receivers | 42/50 | 2 |
| 6 | idea-06 | Individual fixed-QoS feasibility map and active-bound analysis | 42/50 | 2 |
| 7 | idea-10 | Endpoint and singleton QoS cases with power-budget checks | 42/50 | 2 |
| 8 | idea-13 | Independent Python and MATLAB implementations of one model | 42/50 | 2 |
| 9 | idea-14 | Precision and normalized-SNR invariance in the comparison | 42/50 | 2 |
| 10 | idea-15 | Independent-seed Monte Carlo convergence with paired counts | 42/50 | 3 |
| 11 | idea-08 | Equal-channel degeneracy as an equality and optimizer check | 37/50 | 1 |
| 12 | idea-03 | Independent bounded numerical maximization of the constrained split | 37/50 | 2 |
| 13 | idea-09 | Channel-separation sensitivity without changing user pairing | 37/50 | 2 |
| 14 | idea-11 | Low-SNR feasibility limits and conditional expansion checks | 37/50 | 3 |
| 15 | idea-12 | High-SNR conditional limits for optimized fixed-QoS allocation | 37/50 | 3 |

## Evidence to spot-check

- `ideas/idea-01.yaml` and `ideas/novelty/idea-01.yaml`: interval/endpoint proposal,
  precise paper differences, five query references and rationale.
- `ideas/novelty/reviewer-search-receipts.json`: actual reviewer query receipts,
  result URLs, UTC clock readings and failures. Query labels identify calls;
  they are not search-provider internal citation IDs.
- `ideas/ranking.json`, `ideas/sensitivity.json`: deterministic outputs.
- `ara/staging/P3-audit-acceptance.json`: exact receipt mapping and runtime checks.
- `ara/staging/P3-review-effort.json`: permission, actual spawns and unsuccessful trials.
- `to_human/G3-report.md`: generated artifact bindings and gate checks after request.

All full-paper formulation comparisons use the six supplied grounded preprint
texts. Fresh search results are discovery evidence only. Zhu's additional power
order/SIC restrictions, Fair-NOMA's OMA-relative targets and differing OMA
schedulers are explicit transfer boundaries. No published numeric gain or
asymptotic constant is adopted as a measured M11 result.

A relevant pairing-code lead was found in a public previous-works repository;
its exact revision, authorship, paper mapping, license and M11 suitability are
unverified. It is unaccepted and unexecuted. No claim that relevant public code
does not exist is made. The optional individual-QoS paper remains a metadata
lead with failed prior acquisition identity checks.

The search is bounded and purposive. Exact proposed validation layouts and
publication readiness remain unverified. The parent separately made 42 additional
public queries; those are not counted toward the independent five-per-card minimum.
Forbidden-source index hits in parent discovery were excluded without opening
or downloading such pages. Reported absence of injection is not a general web scan.

## PI action

From the repository root, run this command if selecting the recommendation:

```powershell
.\.venv\Scripts\lab.exe gate approve G3 --project m11-noma-qos --select idea-01 --note "P3 dry-run options and evidence reviewed; idea-01 selected; G3 report usable" --json
```

For another eligible option, replace the ID and note accordingly. Type the fresh
confirmation requested by the CLI yourself. Record your actual report-usability
rating in the note. If changes are needed, use `lab gate revise G3` with a reason.
Please do not approve until the generated G3 report shows passing checks.
