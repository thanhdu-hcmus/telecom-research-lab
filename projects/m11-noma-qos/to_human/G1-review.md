# G1 review — M11 toy benchmark

Historical preparation packet. The PI completed this review and approved G1 on
2026-10-10 at 17:22:02 UTC, recorded in commit `2ea3b17`. The exact decision note
is “Scope and synthetic profile reviewed; G1 report usable”. The instructions
below describe the completed handoff and do not request another G1 decision.

## Decision needed now

Accept or revise the proposed scope and synthetic benchmark profile. Also rate
this gate packet usable, or identify what needs improvement. AGENTS.md and the
source plan require the PI's own gate decision; automatic M1–M10 build permission
and a general instruction to continue do not record that scientific decision.

## Review these files

- `../scope.md`: proposed comparison, assumptions and boundaries.
- `../scope.yaml`: executable dry-run scope and project-profile path.
- `../profile.yaml`: synthetic benchmark profile, separate from the dissertation.
- `../execution-plan.md`: seven handoffs and acceptance/usability criteria.
- `G1-report.md`: automated checks and artifact checksums.
- `../ara/trace/sessions/`: AI preparation provenance.

## Proposed scope in brief

Two-user scalar downlink, perfect CSI and ideal SIC. Maximize NOMA sum rate
subject to per-block QoS, and compare with equal-time OMA using identical power,
bandwidth and channel gains. Report infeasibility and paired sample counts.
Derive and verify the conditional NOMA ≥ OMA expectation later. No novelty,
RIS/mmWave dissertation choice or measured improvement is claimed here.

Exact distributions, QoS values, grids and stopping criteria belong to the later
model/protocol gates. The main thesis profile can remain unfinished during this
synthetic benchmark. It will require PI review before original research.

## Record your decision

If acceptable, the PI changes only these review flags after reading the files:

- `../profile.yaml`: `pi_reviewed: true`
- `../scope.yaml`: `thesis_profile_reviewed: true`

Then run in an interactive PowerShell terminal from the repository directory:

```powershell
.\.venv\Scripts\lab.exe gate request G1 --project m11-noma-qos --json
.\.venv\Scripts\lab.exe gate approve G1 --project m11-noma-qos --note "Scope and synthetic profile reviewed; G1 report usable"
```

Use an accurate explanatory note; do not say usable unless that is your judgment.
The CLI shows a fresh confirmation code for the PI to type. Do not share that
code with an agent or ask an agent to enter it. The first command refreshes the
review hashes after the flags change; approval records and commits the decision.

If changes are needed, specify them before approval. Do not approve a packet
whose checks fail. The current intentional failure is the unreviewed flags.

## Current effort and status

P1 entered through the CLI. Scope/profile and handoffs prepared by the main
agent; no specialist spawns, literature retrievals or experiments for M11 yet.
No untrusted paper/repository content was processed for this scope draft.
The statements in this section describe the original P1 draft. Current state:
G1 approved, P2 started, G2–G7 not yet approved; no deviations are open.

After G1 is recorded, the next authorized work is P2's bounded literature review.
M12's reference-paper choice is needed later, not to start this benchmark.
