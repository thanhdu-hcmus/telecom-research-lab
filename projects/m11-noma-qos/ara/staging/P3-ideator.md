# P3 ideator brief

Read AGENTS.md, .codex/agents/ideator.toml and its three skills, approved scope/profile,
research-state.yaml, findings.md, literature/cards, gap-matrix.csv and survey.md,
config/ranking.yaml and lab/models.py IdeaCard. G1/G2 are approved; P3 started.
Approved profile contains historical pending prose; recorded PI decisions govern.
Never change any approved scope/profile/literature/baseline candidate artifact.

Objective: >=15 complete, distinct benchmark design options for the SAME approved
two-user scalar downlink NOMA sum-rate/QoS versus matched equal-time OMA problem.
These are established-method dry-run options, not 15 new scientific contributions.
Each must cover the core comparison and have a distinct analysis/validation focus
or computational method; don't create near-identical renamed cards just to reach 15.
Useful diversity includes exact analytic interval, bounded scalar exhaustive check,
independent numerical optimality check, rate-region construction, deterministic
boundary checks, channel separation, equal-channel equality, heterogeneous fixed
QoS, allocation endpoint cases, feasibility/intersection accounting, high/low-SNR
conditional limits, independent languages, precision/normalization checks and
Monte Carlo convergence. All are proposals; final distributions/grids/seeds/solver
tolerances are deferred to P4/P5, not chosen here.

No objective or physical-assumption changes: no RIS/mmWave/MIMO/uplink, mobility,
learning, imperfect CSI/SIC, different OMA scheduler, blanket weak-power>=half
constraint, dropping infeasible blocks, original novelty or publication-readiness.
Never claim a simulated result or proven M11 theorem; literature findings remain
about cited papers. Falsifiable improvement is a checkable implementation/validation
property relative to a naive implementation, not an unmeasured rate gain.

Own only ideas/idea-01.yaml through idea-15.yaml (more if justified),
ideas/design-options.md and ara/staging/P3-ideator-evidence.json. Do not write
novelty reports/ranking until parent asks after independent audit. Do not select
an idea, enter another phase, run simulations, approve gates, Git operations or
spawn subagents. Save UTF-8 LF explicitly so bound hashes survive Git checkout.

Every card must validate IdeaCard, have >=3 distinct INCLUDED full-paper IDs with
precise overlap/delta and BQ refs. Follow exact schema: problem, method_sketch,
expected_contributions, risks/risk_rating, resources.compute_estimate, months,
target_venue_class, feasibility pass/reasons, novelty verdict/report, scores.
Resource/month estimates are AI planning estimates, not measured runtimes or a
submission promise. Time score follows actual thresholds; benchmark estimates
under three months score 5. Score synthetic benchmark fit honestly. Venue score 1
with >=2 historical included comparator IDs: explain they support scientific
context only, and no recent Q2 suitability claim exists. Approved target is internal
M11 acceptance; do not invent recent venues/comparators or a submission deadline.

During generation set novelty.verdict unclear and report ideas/novelty/<id>.yaml,
explicitly pending independent audit. Established framing is expected, but parent
will populate verdicts from actual reviewer output. Complete generation separately
from screening. Preserve no unpublished-newness claim in expected_contributions.
Return <=15 summary lines, notify parent when cards ready for search/review packet.
