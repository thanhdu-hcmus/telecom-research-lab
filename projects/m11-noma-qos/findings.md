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

## Current P5 R2: PI rewind verified; tested repair applied

PI commit 76525a2 canonically rewound to P5, archiving the initial simulation
inputs and results. G1-G4 remain approved; G5-G7 are invalidated. Native P5
phase start passed. Only lab/verification.py changes among the 51 previous locked
inputs: verifier-key compatibility and a bounded 3600-second execution budget.
The physical protocol, model and simulation sources are byte-identical to R1.
All 123 combined framework and project tests pass, and Ruff passes. A fresh code
commit, relock and 145 manifest reruns are next. The engineering verifier audit
identifies analysis-only P6 supplements; no independent P6 verification is claimed.
The archived initial G5 SVG transport is preserved with a scoped byte attribute.
See ara/staging/P5-rerun-preparation.json. Earlier P6 repair-pending notes are
historical; this rewind authorizes applying the prepared implementation repair.

## Current P5 R2: fresh experiments complete; G5 pending

Following canonical PI rewind 76525a2, the committed code-only repair and fresh
lock produced all 145 planned native jobs with zero resumptions. All 1,015 saved
output files are byte-identical to archived R1, checked from actual old/new bytes
against both generations of manifests. Only lab/verification.py changes among
51 locked inputs. The physical v1 protocol and simulation sources remain unchanged.

All 123 combined tests and Ruff pass. Native collection, conditional statistics,
oracle diagnostics and seeded channel audit were freshly recomputed with their
ordinary integrity checks enabled. The fresh G5 request passes. G1-G4 remain
approved; G5 is pending; G6-G7 are invalidated. Earlier approval and repair-pending
sections above are historical and are preserved.

The finite-grid results retain five joint unresolved deterministic rows and
20 oracle-unresolved rows (four distinct stress cases repeated five times).
Resolved oracle disagreements are zero. Published OMA-subset maximum relative
error remains 0.1716%.
No scientific P6 verifier has run. The author engineering audit identifies 11
coverage findings; its supplement brief does not substitute for independent
verification or an enforced artifact review. Review to_human/G5-rerun-review.md
and the newly generated G5-report.md. M11 remains in progress; M12 is unstarted.

## Current P6: local checker prepared; source review authorization pending

Canonical G5 approval commit398f26d230b7de0194091a36617e0ca0b157f952 was verified, and native P6 phase start passed. G1-G5 are approved; G6-G7 remain invalidated. Earlier G5-pending sections are historical.

The supplemental checker was prepared under analysis/supplement, with 37 isolated tests passing. Its preparation binds 145 planned jobs and 4,718,692 stored rows; preparation is not execution. The shared pinned oracle replay is separately labelled. Parent engineering feedback is not an independent review.

Automatic approval review rejected creating the external review helper because the private source/model/protocol/results payload and separate authenticated OpenAI Codex destination were not specifically authorized. The helper was not created and no review session was launched. A bounded local packet and exact authorization scope are in to_human/P6-code-review-authorization.md. Native and supplemental canonical scientific verification await enforced independent source review. No G6 request or scientific acceptance is claimed.

## Current P6: authorized source review and analysis repairs

The PI explicitly approved the exact bounded private source packet and separate
OpenAI Codex destination, for up to three source-review rounds. This approval is
recorded in analysis/P6-code-review-authorization.json and provenance 0029. It does
not approve a scientific gate or an external numerical-results review. Earlier
source-authorization-pending notes are historical.

The first enforced read-only review completed with recommendation REVISE and 12
findings. Actual parent/child permissions, no-tool reviewer behavior and unchanged
source bytes are retained in analysis/source-review-01. Analysis-only repairs and
red/green evidence now cover report uncertainty, original constraints, objective
comparisons, discrete grid/masks, exact statistical interval interoperability,
selected endpoint/activation, narrow fractional boundaries, underflow, receipts,
cooperative limits and executable conditional claim lineage. The isolated suite
passes 87 tests and seven subtests; all 51 locked inputs remain byte-identical.
These are source and fixture checks, not full canonical scientific verification.

The second authorized enforced review is running on the same approved 19 source
paths and 24 illustrative rows, with only analysis source updated. No native full
verifier or full supplemental run has occurred; no G6 request or scientific
acceptance is claimed. Repair checkpoint:
analysis/source-review-01/parent-repair/repair-checkpoint.json.

## Current P6: three source reviews complete; final repairs tested

The three authorized read-only source-review rounds completed with REVISE.
Round 1 found 12 issues, round 2 six, and round 3 two. Their original source,
findings, actual role/permission audits and negative trials are retained.

The last two analysis-only repairs are complete locally:

- Deterministic lineage records and executed recipes suppress inferential CIs;
  descriptive means and denominators remain. Statistical design and scenario
  come from source manifests; mixed/incompatible recipes fail.
- Native attempt receipts validate fresh P1–P7 items and retain failed prediction
  references, including alongside precision failures. Old stages cannot diagnose
  a new failed invocation.

All 117 JUnit cases pass (110 tests plus seven subtests). Ruff passes. All 51
locked inputs are unchanged. Full canonical verification remains unexecuted,
source readiness is not claimed, and G6/G7 remain invalidated.

An exact 388,193-byte fourth-review packet is prepared: the same 19 approved
source paths and the same 24 illustrative rows; only analysis source changed.
The fourth transmission has not occurred. Additional approval is needed because
the earlier transmission authorization ended after three source-review rounds.
See to_human/P6-additional-source-review-authorization.md.

Encrypted spawn-message transport is retained only locally. Sanitized runtime
metadata preserves provider, role, fork, identifiers and effective-policy audits.
A digest binds the omitted original content; no encrypted transport is published.

## Current P6: fourth source review ready; canonical verification running

The PI approved one fourth source review of the exact388193-byte packet. The
fourth enforced read-only review returned READY with no findings. Actual root
and reviewer permissions, fresh role/fork, OpenAI provider, no reviewer tools,
and unchanged 19-source bindings are retained in analysis/source-review-04.
The source-ready mapping is analysis/source-review-ready.json. This is source
readiness; numerical verification and scientific gate acceptance remain pending.
The prior additional-authorization-pending section is historical.

Full native and independently recomputed supplemental verification launched on
2026-10-12 at15:09UTC, in separate unique execution directories. Both retain
ordinary production integrity guards. The planned supplement covers145 jobs,
4,718,692 rows,4,708 base oracle replays and1,160 tighter replays. Shared replay
remains separately identified. No completion or scientific PASS is claimed.
G1-G5 remain approved; G6/G7 remain invalidated. No external numerical-results
review is authorized by the fourth source-review approval.

## P6 ongoing fractional-boundary diagnostic

At the latest local snapshot, 18 of 145 supplemental jobs and 557,156 rows
have completed, with 396 row discrepancies retained. The first completed
fractional-QoS job has 65 discrepancies, all reproduced in its diagnostic upper
crossing check. An 80-digit comparison of three examples identifies cancellation
in the supplemental subtraction used for out-of-domain diagnostic roots. The
stored values are closer to the high-precision references in these examples.
See docs/evidence/m11-p6-fractional-crossing-diagnostic.json for exact scope.
This explains one job only and does not certify the remaining run. The frozen
reviewed checker, locked inputs, active execution and scientific tolerances have
not been changed. Full results and the combined assessment remain pending.

## P6 native PASS and isolated supplemental repair

The full native operation finished at 2026-10-12 16:05 UTC with PASS and exit zero.
The exact native attempt remains in analysis/supplement/runs; the full report is
analysis/verification.json. G6/G7 remain invalidated and no combined acceptance
is claimed. The active supplement snapshot at 2026-10-12T17:54:12.923689+00:00 is 57/145 jobs,
1,835,108 rows and 2,755 retained discrepancies.

An author-only diagnostic of 56 completed jobs reproduces all 2,750 recorded
errors in crossing fields. The candidate in isolated branch fix/p6-crossing-r5
corrects affine-slope cancellation and records out-of-domain binary64 roundoff
separately. All 133 candidate unit cases pass, including corruption controls.
The canonical reviewed source, active run, locked inputs and scientific
tolerances have not changed. Full results, combined assessment, claim lineage
and enforced numerical-results review remain pending.

## P6 full first attempt completed: combined FAIL

Full coverage is 145 jobs / 4,718,692 rows, with 4,708 base and 1,160 tighter
replays. Native PASS is retained; supplement and combined assessment are FAIL
with G6 request eligibility false. All 2,968 crossing errors were reproduced in
a complete local diagnostic. Source/data/path bindings were rechecked unchanged.
Five stored deterministic rows and 20 base-oracle checks retain uncertainty;
the combined count 55 repeats unresolved/optimality categories. No precision
failure was reported. The 39 generated conditional recipes remain unverified.
Nine per-seed zero-QoS native arithmetic examples are provisional and are not
registered manuscript claims. The isolated candidate author full-row check is
running, and the exact fifth source-review approval remains pending. See
to_human/P6-completed-attempt-status.md and the completed-attempt-01 receipt.
