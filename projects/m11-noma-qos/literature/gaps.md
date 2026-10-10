# M11 benchmark coverage questions

## Interpretation

These questions document what must be derived, implemented and checked for the
approved toy benchmark. They are **not originality claims or proposed scope
changes**. “Not reported” means not established in the cited passages of this
bounded six-paper review; it does not mean absent from all prior literature.
No model, protocol or baseline has been selected here. Page numbers refer to
acquired PDF pages, including preprint versions, as recorded in the cards.

## BQ1 — Fixed QoS and power allocation transfer

**Near works:** `doi:10.1109/jsac.2017.2725618` and
`doi:10.1109/tvt.2017.2689000`.

Zhu et al. formulate individual QoS sum-rate maximization on PDF pp.3 and 6.
The pp.6–7 Proposition 3 proof obtains a nondecreasing sum rate in strong-user
power and a boundary solution. Its feasible set also imposes
`p_strong <= p_weak`, and its stated closed form includes additional threshold
and SIC-stability conditions. Those paper-specific conditions are not silently
part of M11's approved ideal degraded-channel assumptions.

Oviedo and Sadjadpour derive a Fair-NOMA allocation interval on pp.2–3 by
requiring each user's rate to meet its **channel-dependent equal-time OMA rate**.
This provides a useful conditional comparison construction. It does not by
itself supply the arbitrary fixed individual QoS constrained optimizer required
for M11.

**Question to carry forward:** derive the toy feasible interval and optimum
within its actual approved constraints, then relate the result to the two
published constructions. This concerns faithful implementation of established
ideas. An extra power-order restriction would require a scientific decision.

## BQ2 — Resource and scheduler identity

**Near works:** `doi:10.48550/arxiv.1412.2799`,
`doi:10.1109/jsac.2017.2725618` and `doi:10.1109/tvt.2017.2689000`.

Ding et al. use equal-half TDMA for the fixed-power comparison on p.2,
equation (3). Their CR-NOMA sum-rate argument instead compares against serving
only the protected weak user on p.4, equations (23)–(24). This is a different
reference allocation, even within the same paper.

Zhu et al. evaluate multi-channel OFDMA on pp.10–11 with each user assigned
`B/N` bandwidth and waterfilled power. Those reported gains cannot be treated
as numerical results for M11's one-channel equal-time scheduler. Fair-NOMA
pp.1–2 explicitly assigns the whole instantaneous transmit power to the active
OMA user and divides transmission time equally, matching the intended toy
resource accounting more closely.

**Question to carry forward:** state power, bandwidth, channel realization,
noise normalization and time fractions together in every toy comparison. The
missing item is an M11-specific matched reference implementation, not a missing
scientific technique.

## BQ3 — Feasibility, admission and denominator reporting

**Near works:** `doi:10.1109/icc.2018.8422366`,
`doi:10.1109/jsac.2017.2725618` and `doi:10.48550/arxiv.1412.2799`.

The QoS-limits paper pp.2–4 includes SIC decoding in success conditions, explains
that necessary interference limits do not guarantee success, and establishes
fixed-allocation outage-event equality with equal-slot OMA for a common target.
Its p.4 simulations use four users and receive combining; it is not the exact
two-user scalar benchmark or an arbitrary unequal-QoS sum-rate optimizer.

Zhu pp.6–7 provides a QoS feasibility condition in its constrained model.
Ding p.4, equation (21), permits zero strong-user power when the protected
weak-user demand consumes the resource, illustrating why allocation/admission
must be reported. The cited results address feasibility or outage in their own
models; none of these passages supplies the exact M11 report of total sampled
blocks, NOMA-feasible blocks, OMA-feasible blocks and both-feasible paired blocks
under the approved arbitrary-QoS comparison.

**Question to carry forward:** later derive both feasibility tests, check SIC
for every required decoded message under the approved ideal assumptions, and
report all denominator counts. No infeasible sample should disappear from the
record. Protocol details remain for their scientific gate.

## BQ4 — Conditional ideal optimum and limits of transfer

**Near works:** `arxiv:1504.07751`, `doi:10.1109/tvt.2017.2689000`
and `doi:10.1109/comst.2016.2621116`.

Xu et al. p.2 explicitly retain the event in which fixed-power NOMA has a lower
sum rate than TDMA, equations (14)/(18). Their region arguments and Fair-NOMA
pp.2–3 show why a carefully chosen allocation can support an ideal matched
comparison. A fixed power split is not equivalent to a feasible sum-rate
maximizer.

The historical survey p.8 conditions its illustrative rates on perfect
superposition and SIC; pp.34–36 discusses extra decoding complexity, error
propagation, quantization and signalling/processing overhead. These practical
concerns help bound interpretation but are excluded from M11. Historical
statements about unresolved research in that survey are not current novelty
claims.

**Question to carry forward:** establish the conditional theorem for the exact
approved toy set and validate edge cases independently. Neither a measured
M11 result nor universal NOMA superiority follows from the present review.

## Follow-up if P3/P4 needs stronger closest-work evidence

Use the existing lab search/acquisition workflow for focused queries on
single-channel two-user NOMA individual QoS sum-rate optimization and
OMA-feasible QoS rate-region constructions. The attempted individual-QoS paper
has an acquisition identity failure recorded by the scout; do not rely on its
abstract as an included full-paper card. A legitimate full version would be
valuable before transferring any exact formula. No manual download is needed
for the present six-source P2 package.
