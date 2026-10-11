# P3 established benchmark design options

## Status and scope

Fifteen alternative emphases for the same approved M11 two-user scalar downlink
sum-rate/QoS comparison have been authored. They are design options, not fifteen
different scientific problems or novel contributions. Each includes the optimal
feasible NOMA comparison, matched equal-time OMA and full infeasibility reporting.
Only the PI selects an option at G3. Other emphases may be useful later, but this
document selects, combines and locks no scientific protocol.

The independent audit labels all fifteen scientific cores `already-done`, with
five distinct executed searches per option. The exact proposed validation layouts
remain unverified. This supports dry-run eligibility, not original contributions.
Ranking is generated separately. No measured rate gain, simulation or proved M11
theorem exists here.
Generation and screening are separate. The approved profile/scope contain
historical pending prose; recorded G1/G2 approvals and P3 state govern. No
approved scope, literature or baseline artifact was changed.

## Distinct options

| Card | Option | Analysis or validation emphasis | Grounded questions |
| --- | --- | --- | --- |
| idea-01 | Analytic feasible-interval optimizer with an independent scalar oracle | exact feasible interval and endpoint optimality | BQ1, BQ2, BQ4 |
| idea-02 | Bounded exhaustive allocation checks with discretization accounting | grid discretization and narrow-interval coverage | BQ1, BQ3, BQ4 |
| idea-03 | Independent bounded numerical maximization of the constrained split | solver optimality and objective independence | BQ1, BQ2, BQ4 |
| idea-04 | Rate-region construction of a matched OMA comparison witness | constructive conditional comparison proof | BQ1, BQ2, BQ4 |
| idea-05 | Weak-message decoding consistency at both receivers | ideal-SIC decoding order and constraint consistency | BQ1, BQ3, BQ4 |
| idea-06 | Individual fixed-QoS feasibility map and active-bound analysis | heterogeneous QoS and active constraints | BQ1, BQ3 |
| idea-07 | Paired feasibility ledger for conditional rate comparisons | denominators and infeasible-realization retention | BQ2, BQ3, BQ4 |
| idea-08 | Equal-channel degeneracy as an equality and optimizer check | equal ordered gains and flat-objective handling | BQ1, BQ2, BQ4 |
| idea-09 | Channel-separation sensitivity without changing user pairing | gain contrast and conditional interpretation | BQ2, BQ3, BQ4 |
| idea-10 | Endpoint and singleton QoS cases with power-budget checks | zero-target and resource-exhausting boundaries | BQ1, BQ3, BQ4 |
| idea-11 | Low-SNR feasibility limits and conditional expansion checks | small-power limits with fixed QoS retained | BQ1, BQ3, BQ4 |
| idea-12 | High-SNR conditional limits for optimized fixed-QoS allocation | asymptotic allocation and rate checks | BQ1, BQ2, BQ4 |
| idea-13 | Independent Python and MATLAB implementations of one model | language-independent rate and feasibility agreement | BQ1, BQ2, BQ3, BQ4 |
| idea-14 | Precision and normalized-SNR invariance in the comparison | numerical cancellation and conversion invariants | BQ1, BQ2, BQ4 |
| idea-15 | Independent-seed Monte Carlo convergence with paired counts | sampling uncertainty and conditional-statistic repeatability | BQ2, BQ3, BQ4 |

Cards 01-03 use different optimum checks: closed form with an oracle,
resolution-accounted exhaustive evaluation and independent bounded numerical
optimization. Card 04 seeks a constructive matched-OMA witness. Cards 05-07
focus on decoding consistency, individual-QoS bounds and paired accounting.
Cards 08-12 inspect separate equal-channel, separation, allocation-endpoint
and low/high-SNR regimes. Cards 13-15 emphasize independent implementations,
numerical representation and sampling convergence. These are complementary
benchmark emphases with distinct failures and evidence, not renamed new methods.

## Shared safeguards

- Preserve exactly the approved physical assumptions, sum-rate objective and OMA scheduler.
- Add no blanket weak-power-at-least-half, practical SIC margin, extra users or pairing policy.
- Do not replace fixed individual QoS with common-target or OMA-relative fairness QoS.
- Leave all distributions, targets, SNR grids, seeds, stopping rules and tolerances to G4/G5.
- Import no published numerical gain or asymptotic constant as a measured M11 result.
- Ground each card in three distinct included full-paper IDs with page-based overlap/delta.
- Positive-QoS low-SNR cases can be infeasible; high-SNR limits need derived regimes.
- An empty both-feasible set means unavailable conditional statistics, not zero gain.

## Planning estimates and scores

Resource and month estimates are AI planning estimates, not measurements,
submission promises or protocol caps. Each estimate is under three months,
so its configured time score is 5. Fit scores concern only the synthetic
benchmark profile; specialized alternatives acknowledge narrower reuse.
Venue score is 1 for every card. The historical included comparator IDs support
scientific context, while no recent Q2 suitability or submission target is
claimed. Do not inflate that score to force a publication claim. These scores
are inputs to the deterministic ranking saved in `ranking.json`; they
do not imply a PI decision.

## Handoff and checks

All fifteen YAML cards validate `lab.models.IdeaCard`; every closest-work and
venue-context ID belongs to the six included P2 cards. Independent reports are
saved in `ideas/novelty/`; the parent acceptance receipt is
`ara/staging/P3-audit-acceptance.json`. All verdicts retain established-method
framing. Any unclear card would remain ineligible. Generation evidence is stored at
`ara/staging/P3-ideator-evidence.json`. During generation, the ideator performed
no simulations, later phase transitions, Git operations or gate decisions.
The parent subsequently accepted the independent audit and generated ranking
and sensitivity outputs. Scientific selection remains pending at G3.
