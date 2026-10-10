# Remaining-work audit

## Current boundary

M0–M10 software acceptance is complete, including the successful PI Overleaf
check and `test.pdf` receipt. M11's actual seven-gate dry run and M12's published
reference reproduction remain unfinished. The earlier isolated software smoke
fixture used test-only gate substitutes and does not satisfy either milestone.

The PI asked to continue the omitted work. This authorizes preparation and fixes;
the source plan and AGENTS.md still reserve scientific decisions for the PI.

## Omissions addressed

| Finding | Change | Remaining scientific action |
|---|---|---|
| M11 uses an established problem, but G3 rejected established methods | Explicit dry-run scope; truthful already-done verdicts can rank | PI reviews mode at G1 and selects at G3 |
| M12 prescribed skipping ideation, while G3 required fifteen ideas | Typed reproduction/ablation selection and plan; explicit G3 selection retained | PI selects the reference and approves its reproduction plan |
| Ranking and baseline YAML settings were partly hard-coded | Runtime uses configured thresholds, points, agreement and tie breakers; policies enter gate snapshots | Review policy changes with the affected gate |
| Documented --note, --summary and deviation flags did not match required positional arguments | Explicit named CLI options and parsing checks | None for software changes |
| Global thesis profile was an empty template | Unreviewed draft from existing 2026-09-28 workspace notes; missing inputs remain explicit | PI completes and reviews it before real research |
| M11 scope and handoffs had not been prepared | Project m11-noma-qos, synthetic profile, scope, acceptance plan and G1 packet | G1 scope/profile review and report usability rating |
| Plan review still said Overleaf confirmation was pending | Corrected to reference the recorded successful check | None |
| Third-party environments recorded setup but lacked installed transitive versions | Resolved requirements and runtime/source/review checksums captured inside each isolated environment | Reproduce the actual M12 baseline and pin its evidence |
| MATLAB physics used assertions without the prescribed unit-test runner | Added eight matlab.unittest physics tests and a separate R2021b acceptance runner | None for the software runner |
| Old M10 finalization could reset later milestone progress | Preserve active M11/M12 status and unresolved work | None |
| Verification receipts could hash sources after they changed during checks | Snapshot sources before checks and require unchanged hashes at completion | None |

## M11 work remaining

G1 is pending. Its automated check deliberately fails until the PI marks the
scope/profile reviewed; no agent marks those flags. P2–P7 remain unstarted. Each
phase needs its actual evidence, specialist handoffs, validation, PI decision and
report usability rating. The proposed NOMA/OMA comparison states matched budgets,
equal-time scheduling, ideal SIC and explicit feasible-case handling; the
conditional prediction must be derived and checked later.

## M12 work remaining

The reference paper is unspecified. Prefer the PI's own published RIS/NOMA work
with available code/data; otherwise code_scout can propose an official-code IEEE
Transactions reference for PI selection. Narrow P2 to the selected paper and
references, then record the reproduction/ablation choice at G3 and complete
P4–P7. Reference figures, numeric agreement and actual manuscript quality must
be demonstrated; no reproduction is claimed yet.

## Optional capabilities and acceptance limits

- Gemini remains unavailable; independent manual review packets are available.
- A DL workstation route is unspecified. M11 is a CPU benchmark and does not
  require one; real DL work needs an actual configured route and execution.
- Scholarly keys/contact email and SJR data remain optional configuration inputs.
- Overleaf ZIP export is accepted. Git push is conditional on the PI's Overleaf
  plan supporting Git integration; that capability has not been confirmed.
- Third-party environments still require source/dependency/licence/data review.
  Installed versions/origins are captured; this is not an artifact-hash lockfile
  or proof that the selected reference figures have been reproduced.
- Existing built-in verification covers its supported simulation fixture. M11's
  optimization/QoS case needs its own independent verifier and evidence contract.
- MATLAB physics assertions and the standard unit-test runner have separate
  receipts. See `docs/evidence/post-m10-matlab-unittest.json` for the latter.

## Evidence and failures

Post-M10 regression evidence is recorded separately from historical M5–M10
acceptance. See `docs/evidence/post-m10-audit-deterministic.json` and
`docs/evidence/post-m10-audit-failures.json`. Initial targeted checks encountered
Windows temporary/cache directory access errors. Rerunning with workspace-local
directories exposed an incomplete synthetic test fixture (missing reference
results); that fixture was corrected without weakening production validation.
The real isolated environment smoke test is in
`docs/evidence/post-m10-baseline-environment.json`; it installs the framework's
existing pinned NumPy version and records the actual runtime and resolved package
versions. It exercises software setup only and reproduces no published figure.

Implementation documentation was checked through Context7 against primary
[uv environment inspection](https://github.com/astral-sh/uv/blob/main/docs/pip/inspection.md),
[uv Python environments](https://github.com/astral-sh/uv/blob/main/docs/pip/environments.md),
[MATLAB function-based tests](https://www.mathworks.com/help/matlab/matlab_prog/run-tests-in-editor.html)
and [MATLAB verification APIs](https://www.mathworks.com/help/matlab/ref/matlab.unittest.qualifications.verifiable.verifyequal.html).

No original result, PI approval, usability rating or publication selection is
inferred from these software checks.
