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

## Current P4: independent critique complete

The PI approved the bounded external model review in provenance session0014.
Two actual named read-only model_critic rounds recommended ready and reported
zero actionable findings; both complete eleven checklist items and six rigor
dimensions. The parent clarified SINR/rate terminology and zero-branch output
assignments between rounds. Final current model validation and all13 bounded
symbolic checks pass. No approved assumptions, objectives or baselines changed.

The exact model proves the full QoS interval and endpoint optimizer, and that
matched equal-time OMA feasibility implies NOMA feasibility. On both-feasible
blocks optimal NOMA sum is strictly greater when B>A and equal when A=B.
These are ideal-model derivations, not measured simulation results or novelty.
Scalar-oracle implementation, numerical certificates and unresolved statuses,
sampling settings, tolerances and uncertainty reporting remain P5 proposals.
G4 review is ready for a separate PI decision; M11 remains in progress and M12
remains unstarted. Earlier permission-pending sections are historical.

## Current P5: G4 approval verified

PI commit08808d8 approves the model and rates G4 usable. P5 phase start passed. Protocol and implementation are being prepared; simulations have not started. Historical pending statements above refer to earlier states. Approved G1-G4 artifacts remain intact.

## Current P5: experiments complete, G5 pending

The user's explicit test and P5 execution request is retained in session0018.
All 31 targeted simulation/physics tests passed. The first framework attempt had
49 passes and 41 setup errors from the default Windows temporary-folder ACL;
a fresh verified workspace basetemp and disabled cache plugin yielded 90 passes.
No source fix or simulation relock was needed; the failed attempt is retained.

The committed v1 protocol produced 145 completed manifest jobs: 4,718,592 Monte
Carlo scenario evaluations plus 100 deterministic rows. All manifests, outputs
and 51 locked input bindings validate. The 393,216 unique seeded channel pairs
reproduce exactly and are reused across the 12 settings, not independent grid
replicates. All conditional rate intervals meet the declared 1% halfwidth target.
There are zero OMA-only feasible blocks, zero negative paired differences beyond
the declared tolerance and zero candidate rate/SIC violations in this finite grid.

The 4708 original-SINR oracle checks have status counts {'feasible': 4129, 'infeasible': 559, 'unresolved': 20}.
Resolved feasibility/objective disagreements: 0. Twenty unresolved oracle rows
represent four distinct deterministic stress cases; five joint unresolved rows
represent the repeated fractional boundary. Unresolved outcomes are retained,
not relabeled. Maximum resolved objective error: 6.66755539668884e-12.
The six published OMA-subset points agree within 0.1716% (declared limit 5%);
this does not reproduce the Fair-NOMA allocation curves or every paper figure.

The protocol's incorrect root-LICENSE reference has a separate documentary
erratum; locked input bytes and numerical settings are unchanged. No upstream
software is accepted or executed, and no repository-wide license is claimed.
G5 automated checks pass; review to_human/G5-review.md and G5-report.md. The
lab-orchestrator rule requires the PI G5 decision before independent P6
verification. M11 remains in progress; M12 remains unstarted. Earlier preparation
and pending-test sections are historical. Approved G1-G4 bindings remain intact.
