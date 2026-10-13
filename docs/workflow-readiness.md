# Telecom research workflow readiness

## Current goal and status

The PI's current goal is to finish the agent team and create an end-to-end
telecommunications research workflow. Development should prioritize usable
orchestration, artifact handoffs, recovery, and documentation. Further full M11
evaluation passes are not scheduled as part of this handoff.

The M0-M10 framework is built and has recorded software acceptance. It contains
the main-session orchestrator, eleven specialist configurations, and twenty-one
skills. The simulation-to-manuscript integration fixture has exercised locking,
execution, verified resume, collection, verification, executable claims, figures,
citations, compilation, and ZIP export. The PI also confirmed Overleaf compilation.

These checks establish software readiness within their recorded scope. The
integration fixture uses test-only phase guards; it is not an actual seven-gate
research acceptance run. M11 and M12 remain incomplete under the original plan.

## Agent team and handoffs

The main Codex session orchestrates the following phases. Each specialist gets a
brief with input paths, output paths and schemas, done criteria, and forbidden
actions. Accept its output only after validation. At most three specialists run
concurrently, at depth one; scientific gates remain actual PI decisions.

| Phase | Specialists | Handoff | PI gate |
|---|---|---|---|
| P1: scope | Orchestrator with PI | Reviewed scope and project profile | G1 |
| P2: literature and baselines | lit_scout, paper_analyst, code_scout | Screened papers, grounded cards, gap matrix, survey, baseline candidates | G2 |
| P3: idea selection | ideator, novelty_auditor | Audited ideas, ranking and sensitivity; or reproduction selection | G3 |
| P4: system model | system_modeler, model_critic | Assumptions, notation, predictions, symbolic checks and independent critique | G4 |
| P5: implementation and experiments | sim_engineer | Committed protocol, reviewed baseline, locked sources, raw outputs and manifests | G5 |
| P6: verification | results_verifier | Independent checks, uncertainty, discrepancies and executable claim lineage | G6 |
| P7: manuscript | paper_writer, paper_reviewer | Traced numbers, verified citations, figures, compiled manuscript and clean export | G7 |

Authors and independent reviewers work sequentially when the reviewer needs the
author's artifact. Reviewers receive artifacts rather than author reasoning.
Effective read-only permissions must be audited; role defaults alone do not
establish isolation.

## Start and resume

Open the repository in Codex and use [the user guide](user-guide.md) for the
existing commands. Ask the orchestrator to initialize or resume a named project,
read its research state and findings, identify the next permitted phase, and
delegate file-based tasks. On resume, it must recheck approvals and current
artifact bindings before continuing.

For a real project, review the thesis/project profile, scope and target venues
before G1. For a reproduction, identify the reference paper and available code
and data. Execution continues within an approved phase and stops at the next PI
gate. This workflow does not include automatic scientific approval or submission.

## Evaluation budget

Use existing acceptance receipts when reporting what has already been verified.
For future implementation changes, start with affected unit and contract checks
and a small isolated integration fixture. A shortened scientific run requires
its own declared scope; it cannot replace the approved full protocol's evidence.

Full-data verification belongs to a deliberately scheduled scientific acceptance
step, not every documentation or orchestration change. Keep failed and
inconclusive receipts. Record scope, rows, seeds, sources and commands for every
new check; distinguish software checks from accepted scientific results.

## Parallel execution: available and proposed

Agent parallelism is configured in `.codex/config.toml`. Independent literature
tasks can run together within the three-specialist limit. This is separate from
CPU parallelism for numerical jobs.

The current `lab sim run` and M11 supplemental checker process numerical jobs
sequentially. There is no implemented `--workers` option. Launching multiple full
instances is not job partitioning; simulation also has a project run lock.

The workstation reports fourteen physical cores and twenty logical processors.
If full verification is resumed, a proposed bounded worker pool would start with
four processes, each handling a distinct job and writing isolated diagnostics.
The parent would perform the original integrity guards, merge results in fixed
manifest order, check complete/nonduplicate coverage, and preserve all existing
tolerances, unresolved states and evidence bindings. Budgets would need to cover
the complete worker pool. Serial and parallel semantic results must agree;
runtime fields will differ.

This is a proposal, not an implemented or benchmarked capability. Shared disk
access, tracing, job imbalance and final integrity checks limit speedup. Parallel
execution would reduce elapsed computation; it would not resolve uncertain
mathematical certificates. The existing scientific sources remain unchanged.

## Retained M11 status

No M11 evaluation process was active when this handoff was prepared. The second
canonical pass finished 145 jobs and 4,718,692 rows with zero execution errors.
Native verification is PASS; the supplement is
CHECKED_WITH_DECLARED_UNRESOLVED; the combined assessment is INCONCLUSIVE.
G1-G5 are approved; G6/G7 remain invalidated. Five stored deterministic rows and
twenty base-oracle checks remain unresolved.

The first scoped deterministic numerical review finished with limitations and
no open findings. The second statistical packet remains local and untransmitted.
No new review session or full evaluation was launched for this readiness handoff.

See [the remaining-work audit](remaining-work-audit.md) for the original M11/M12
acceptance requirements and [the current M11 status](../projects/m11-noma-qos/to_human/P6-completed-attempt-status.md)
for the retained scientific receipts. They remain available if research
acceptance is resumed later.

## Evidence already available

- [Framework acceptance](acceptance-m5-m10.md): specialist evaluations and tooling acceptance.
- [Simulation-to-manuscript integration](evidence/m8-m10-local-integration.json): isolated software fixture.
- [Post-M10 acceptance](evidence/post-m10-audit-acceptance.json): subsequent regression and MATLAB checks.
- [Overleaf confirmation](evidence/m10-overleaf-confirmation.json): PI confirmation and inspected PDF.
- [Implementation state](../implementation-state.json): software and research status kept distinct.
