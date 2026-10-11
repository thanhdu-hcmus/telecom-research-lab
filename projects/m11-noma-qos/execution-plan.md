# M11 handoffs and acceptance

Status: G1 approved by the PI on 2026-10-10; P2 entered through the CLI.
G2 is approved and rated usable; P3 has started. P4–P7 remain planned.

| Phase | Planned work | Required PI action |
|---|---|---|
| P1 | Review scope and synthetic benchmark profile | G1 and report usability |
| P2 | Bounded foundational NOMA/OMA/QoS review; grounded full-paper cards and gap matrix | G2 and evidence spot-check |
| P3 | At least 15 complete benchmark idea cards; truthful novelty audit, ranking and sensitivity | G3 explicit eligible selection |
| P4 | Ordered channel model, matched budgets, QoS interval and conditional prediction; independent critique | G4 assumptions and critique acceptance |
| P5 | Reviewed reference, locked committed protocol, physics checks, seeded runs and manifests | G5 protocol and execution review |
| P6 | Independent feasibility, paired comparison, uncertainty and prediction checks; executable claims | G6 evidence acceptance |
| P7 | Grounded IEEE-format manuscript, number trace, citation verification, review and clean export | G7 manuscript acceptance |

Use named specialists from `.codex/agents` when the approved phase calls for them.
Record actual spawns and permissions. No specialist was spawned for this P1 draft.
Never substitute software-fixture gate mocks for PI decisions in this project.

## PI report usability record

At approval, include the actual usability judgment and
any issues in the PI's explanatory note. This table is updated only from recorded
decisions; no rating is inferred from general permission to continue.

| Gate | PI usability rating | Decision evidence |
|---|---|---|
| G1 | usable | PI decision `2ea3b17`; note: “Scope and synthetic profile reviewed; G1 report usable” |
| G2 | usable | PI decision `b3709e0`; note: “Bounded P2 corpus and evidence spot-checked; G2 report usable” |
| G3 | usable | PI decision cb4061a; idea-01 selected |
| G4 | pending | none |
| G5 | pending | none |
| G6 | pending | none |
| G7 | pending | none |

M11 is complete only when all acceptance conditions in the source plan hold.

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

## Current P4: model development

The PI approved G3 in commit cb4061a, selecting idea-01 and recording G3 report
usability as usable. P4 started successfully. The named system_modeler is preparing
the exact QoS interval, optimizer, degeneracies, matched OMA comparison and
falsifiable predictions. Independent critique and G4 remain pending. No
implementation protocol or simulation has started.

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
