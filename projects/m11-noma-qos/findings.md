# Findings

## Current understanding

The plan specifies an established two-user NOMA benchmark for M11. The PI
approved the scope and synthetic profile at G1 on 2026-10-10 (decision commit
`2ea3b17`), with the explicit rating “G1 report usable”. The PI approved G2 in
commit `b3709e0`, noting “Bounded P2 corpus and evidence spot-checked; G2 report usable”.
P2's accepted bounded review has ten queries, 148 raw records, 122 unique candidates, six included
full papers and 116 exclusions, with no pending screening decisions. P3 has started
to generate and audit established benchmark options. No approved
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

- Are the later gate reports usable? G1/G2 are explicitly rated usable; record the
  PI's actual rating at each remaining gate.
- Which eligible benchmark option will the PI select at G3 after the audit and
  ranking? Model and protocol decisions remain at later gates.
- Which reference paper should be used for M12 after M11 is accepted?

## P3 draft handoff and review authorization (historical)

Fifteen established-benchmark design options are drafted in `ideas/` with an
overview in `ideas/design-options.md`. Parent checks confirm all schemas and
included-paper references, LF text, and unchanged G1/G2 approved bindings.
Their novelty remains `unclear`; independent reports and ranking are pending.

The separate read-only Codex novelty audit was rejected before launch by
automatic approval review because it would process unpublished local artifacts
externally and use live searches without explicit payload/destination approval.
No retry or workaround was used. The finite review packet and permission request
are described in `to_human/P3-review-authorization.md`; local check evidence is
`ara/staging/P3-parent-review.json`. G3 is not ready/requested. No model or
simulation has started.

## Current P3: audit and ranking ready for G3

The PI explicitly approved the bounded external audit (“Okie, approved”);
provenance session 2026-10-11-0007 records this permission, not a scientific gate.
The completed named independent reviewer made 82 query requests (81 distinct
strings), with five distinct card-specific searches for each of 15 options.
All scientific-core verdicts are already-done; exact validation layouts remain
prospective. Parent checks matched all per-card queries to actual receipts and
confirmed read-only runtime and unchanged supplied artifacts. Two preliminary
attempts failed and were not accepted as complete audits.

Ranking/sensitivity pass. The top three are idea-01, idea-07 and idea-02, all
42/50, unchanged across seven tested weight combinations. Ten cards tie at 42;
time/venue dimensions are flat, so risk and ID also determine order. Idea-01 is
recommended for an inspectable analytic solution with an independent oracle;
this is not a PI selection or a novelty/publication claim. Full G1/G2 bindings
remain intact. No model, protocol or simulation has started.

See to_human/G3-review.md and the generated G3-report.md for the concrete decision
packet. The lab-orchestrator gate rule requires the PI's explicit G3 selection
before P4. M11 remains in progress; M12 remains unstarted.

## Current P4: PI selection verified

Canonical G3 decision cb4061a selects idea-01 and rates the report usable.
P4 phase start passed. Earlier P3 pending/selection statements above describe
the pre-decision state. Model artifacts and independent critique are in progress;
no approved G4 model, protocol or simulation exists yet. Provenance session 0012
corrects the stale-state assertions mistakenly recorded in session 0011.

## P4 draft checks and independent review permission

The named system_modeler completed seven draft artifacts. Parent schema checks
pass (7 assumptions, 7 predictions, 40 notation entries), and all 13 bounded
symbolic checks pass. These are local checks, not an independent critique or
measured simulation results. The artifact review packet was regenerated after
a pseudocode clarification.

Automatic approval review rejected the isolated external model_critic launch
before any process started because previous permission covered P3 only. The
exact new P4 payload is prepared locally, not transmitted. Explicit bounded
authorization is requested in to_human/P4-review-authorization.md. G4 is not
requested; no independent verdict or numerical protocol is claimed.
