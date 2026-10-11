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

## Current P6: G5 approved; framework repair awaits PI rewind

PI commit b289a06 records G5 approval. Native P6 phase start passed, but the
entrypoint preflight stopped before any verifier ran: the protocol's `verifier`
key is not recognized by the framework's `verification_entrypoint` reader.
An isolated compatibility patch preserves the native independence/pinning
checks and rejects conflicting keys. A bounded 3600-second execution budget is
also proposed; no actual P6 timeout is claimed. The original-code failed trials
are retained, seven final targeted tests pass, and the isolated full regression
passes all 97 tests. Ruff passes. All 51 canonical locked inputs remain unchanged.

Review to_human/P6-repair.md and ara/staging/P6-fix-preparation.json. Applying the
fix changes a locked framework input; the PI-only canonical rewind to P5 must
precede relocking and fresh manifest runs. Existing data will be archived by the
rewind. G1-G5 currently remain approved; G6/G7 are not started. No independent
P6 result, external reviewer verdict or scientific acceptance is claimed. M11
remains in progress; M12 remains unstarted. Earlier pending statements above
are historical.
