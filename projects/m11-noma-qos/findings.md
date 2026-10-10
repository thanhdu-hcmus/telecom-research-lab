# Findings

## Current understanding

The plan specifies an established two-user NOMA benchmark for M11. The PI
approved the scope and synthetic profile at G1 on 2026-10-10 (decision commit
`2ea3b17`), with the explicit rating “G1 report usable”. P2's bounded review is
prepared for G2: ten queries, 148 raw records, 122 unique candidates, six included
full papers and 116 exclusions, with no pending screening decisions. No approved
model, protocol, simulation or manuscript exists for this project.

## Supported claims

Literature-supported findings, with exact paper IDs and PDF pages in
`literature/survey.md`, `literature/gaps.md` and the six cards:

- Xu PDF p.2 retains a fixed-power NOMA sum-rate loss event. A fixed split cannot
  be treated as a constrained sum-rate optimum.
- Fair-NOMA PDF pp.2–3 constructs an interval that meets each user's equal-time
  OMA rate. These channel-dependent thresholds differ from arbitrary fixed QoS.
- Zhu PDF pp.3 and 6–7 supplies a related QoS boundary optimizer with additional
  paper-specific power-order and SIC-stability restrictions. They are not silently
  transferred into the approved scope.
- OMA definitions differ across papers: equal-time/full active-slot power,
  primary-user-only service and waterfilled multichannel OFDMA. Published gains
  cannot be imported across these definitions.
- QoS-limits PDF pp.3–4 distinguishes necessary interference bounds from success
  and outage-event equality from capacity equality.

These are findings about the cited works. The conditional M11 comparison remains
an expectation to derive and verify later, not a measured project result.

## Lessons and constraints

Keep resource budgets, scheduling, QoS and feasibility reporting explicit.
Dry-run mode permits established-method cards without relabelling them novel.
Scientific gate approvals and report usability ratings belong to the PI.
The four `BQ` matrix entries are benchmark validation questions, not novelty
claims. The review is purposive and bounded, with related relevant works omitted
explicitly; it is not a comprehensive systematic review.

No exact benchmark code package was verified in the bounded code search. Four
related repositories are rejected for scope or paper-mapping reasons; two later
analytic implementation proposals are unimplemented and unaccepted. No third-party
code was executed. One optional QoS paper failed acquisition identity checks; both
attempts remain in the retrieval report, with no manual download required now.

## Open questions

- Are the later gate reports usable? G1 is explicitly rated usable; record the
  PI's actual rating at each remaining gate.
- Does the PI accept the bounded corpus, evidence cards and comparison questions
  at G2? Model, idea selection and protocol decisions remain at later gates.
- Which reference paper should be used for M12 after M11 is accepted?
