# Bounded P2 synthesis — established two-user NOMA/QoS benchmark

## Scope and evidential status

G1 approved a dry-run benchmark: scalar two-user downlink, ordered channel
gains, perfect instantaneous CSI and ideal SIC; matched power, bandwidth,
channel realizations and per-block QoS; equal-time OMA; explicit feasibility
accounting. This review supports later derivation and implementation of an
established problem. It chooses no new assumptions or scientific protocol and
makes no originality, publication-readiness or literature-completeness claim.

Six legitimate full papers are included, with page-grounded cards. They span
2014–2018 publication/preprint metadata, plus revised preprint dates. The scout's
`screening.yaml`, PRISMA and coverage report supply acquisition and search
counts, source failures and limits. A complete PDF being available does not
mean every page was required for extraction; inspected pages are listed in
`ara/staging/P2-paper-analyst-evidence.json`. Unknown code availability and
unneeded citation counts remain null. Preprints and later journal records must
not be conflated when assigning title, date, equations or page numbers.

## Comparison map

| Included source | Grounded mechanism | Reference and QoS | Transfer boundary for M11 |
| --- | --- | --- | --- |
| Xu et al., `arxiv:1504.07751` | Gaussian broadcast rate-region geometry and paired Rayleigh performance events (pp.1–4) | Generic TDMA shares; equal halves for probability analysis; fixed NOMA split | Establishes comparison geometry and retains fixed-split loss events; does not solve arbitrary fixed-QoS optimization |
| Ding et al., `doi:10.48550/arxiv.1412.2799` | Fixed-power pairing and channel-dependent CR allocation (pp.2–4) | Equal-half TDMA for F-NOMA; primary-only reference for CR sum rate | Pairing, fairness and admission depend on objective/reference; one comparison cannot replace the other |
| Zhu et al., `doi:10.1109/jsac.2017.2725618` | Within-channel optimum and multi-channel budget allocation (pp.6–7) | Individual QoS plus additional power-order/SIC-stability constraints; waterfilled OFDMA baseline (pp.10–11) | Closest sum-rate/QoS optimizer, but its extra constraints and multichannel baseline must not be copied into the toy |
| Oviedo and Sadjadpour, `doi:10.1109/tvt.2017.2689000` | Fair-NOMA interval giving each user at least OMA rate (pp.2–3); K-user extension (p.7) | Equal-time OMA at full active-slot power; OMA-dependent fairness thresholds | Closest matched-resource comparison construction; thresholds differ from arbitrary fixed QoS |
| Oviedo and Sadjadpour, `doi:10.1109/icc.2018.8422366` | QoS/SIC success conditions and fixed power with OMA outage-event equality (pp.2–4) | Common target for K users and equal-slot OMA | Outage-event equality is explicitly different from instantaneous capacity equality; combining/multiuser evaluation is outside toy |
| Islam et al., `doi:10.1109/comst.2016.2621116` | Historical survey and illustrative scalar NOMA model (pp.7–8) | Multiple published models and practical contexts | Context and assumption caveats, not an exact optimizer or contemporary novelty proof |

## 1. Rate regions and chosen allocations

Xu pp.1–2 relates superposition/SIC rates to a scalar Gaussian broadcast rate
region and the TDMA line. Their sum-rate monotonicity and concavity arguments
are useful for later proof. The paper nevertheless treats fixed power in its
probability study (p.3), and its p.2 event definitions explicitly include a
NOMA sum-rate loss relative to TDMA. Ding pp.2–3 likewise analyzes the
probability of fixed-power loss and contrasting individual-rate behavior.
These statements concern chosen allocations under their models. They are not
counterexamples to, or proofs of, the exact M11 optimized feasible comparison.

Fair-NOMA solves the two individual `NOMA >= equal-time OMA` inequalities on
pp.2–3. Its channel-dependent interval provides a constructive comparison point
under ideal SIC and matched active-slot power. The arbitrary fixed QoS toy
problem still requires its own admissible interval and feasibility derivation.
P2 supplies evidence for this task; it does not declare the task solved.

## 2. QoS-constrained sum-rate allocation

Zhu pp.6–7 characterizes a two-user per-channel QoS sum-rate optimizer, with
larger systems obtained by allocating channel budgets. Its derivative proof
shows why strong-user rate increases can improve the sum objective for ordered
CNRs, while the weak-user rate constraint controls the boundary allocation.
The conditional closed form also includes a power-order constraint and
SIC-stability restrictions, including the stated weak-user threshold condition.
M11 only approves ordering by channel gain; it does **not** automatically approve
`p_strong <= p_weak`. Any copied condition must be justified or separately
approved, rather than introduced through a literature citation.

Fair-NOMA and the common-target fixed-power QoS paper answer related but
different questions. Fair-NOMA requires OMA-relative per-user rates; the
QoS-limits paper pp.3–4 makes decoding and outage events coincide for a common
rate. The latter expressly warns that this does not make instantaneous NOMA
and OMA capacities equal (p.4). Neither statement substitutes for arbitrary
individual fixed-QoS sum-rate maximization.

## 3. Fair comparison and infeasibility

A comparison must identify the orthogonal resource policy. Ding p.2 uses
half-time TDMA while its CR sum-rate proof on p.4 uses only the primary user.
Zhu pp.10–11 compares a multi-channel solution to bandwidth-partitioned,
waterfilled OFDMA. Fair-NOMA pp.1–2 states equal time and full active-slot
transmit power. Their numerical gains are tied to those references and cannot
be treated as measured toy results.

Feasibility also needs its own accounting. Zhu pp.6–7 provides conditions in
its model; Ding p.4 permits zero secondary allocation when primary QoS uses the
resource. The QoS-limits paper pp.2–3 includes both own-message and SIC decoding
success and states that necessary interference limits are insufficient by
themselves. M11 must later retain infeasible realizations and distinguish
NOMA feasibility, OMA feasibility and their intersection. Sum-rate differences
are paired only on the both-feasible set, with denominator counts visible.
No specific SNR grid, channel law, QoS grid, seeds or tolerances is selected
by this literature phase.

## 4. Assumptions and practical interpretation

The scalar papers use interference-free strong-user rates after cancellation.
These are ideal achievable-rate models, not demonstrations of physical-layer
SIC accuracy. The survey p.8 says perfect superposition/SIC is assumed for its
illustrative rates; pp.34–36 identifies decoding complexity, error propagation,
quantization and CSI/order signalling overhead. These concerns limit practical
extrapolation. They do not expand the approved dry-run scope.

The survey is a historical context source. Its dated standardization status or
claims about unanswered questions are not current facts. Likewise, RIS,
mmWave, MIMO, mobility and residual-SIC conclusions from broader sources cannot
serve as exact proofs of the approved two-user scalar model.

## Handoff

The four `BQ` items in `gaps.md` and `gap-matrix.csv` are benchmark coverage
questions. They guide truthful P3 established-method cards and later P4/P5
proof/protocol work, subject to actual PI gates. The existing literature
already supports a clear **established-work** framing; the bounded corpus does
not support a novel-research claim. Baseline implementation candidates and
third-party code evidence are assessed separately in `baselines/candidates.yaml`;
no paper has been numerically reproduced in this phase.
