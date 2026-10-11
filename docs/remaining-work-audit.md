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
| Local secret scan silently scanned no files after a Git ownership rejection | Explicit verified Git inventory and bounded file batches; missing inventory fails closed; canary regressions | None |

## M11 work remaining

Current status: G1–G4 approved. The canonical PI rewind to P5 invalidated the
first G5 approval and G6–G7. P5 R2 applies a tested verifier-entrypoint repair,
with the physical protocol unchanged, and completes 145 fresh native jobs.
All 123 combined tests pass. Actual output bytes match archived R1 and fresh
collection/statistics/channel/oracle summaries are regenerated. The new G5
request passes and awaits PI review in
`projects/m11-noma-qos/to_human/G5-rerun-review.md`.

After renewed G5 approval, P6 must execute the pinned verifier and independently
address the 11 coverage findings with analysis-only supplements, then obtain
enforced independent artifact review and a PI G6 decision. P7 still requires an
evidence-traced manuscript, verified citations, compilation, independent paper
review and PI G7 approval/report usability judgment. No P6 result or M11
completion is claimed. Earlier G1-pending preparation statements are historical.

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

The first audit push passed Linux CI tests but failed the secret scan on checksum
fields. `docs/evidence/post-m10-secret-scan-debug.json` records the local empty-scan
root cause and individual cryptographic checks of those false positives. The
audited baseline marks only those exact hashes as non-secrets; detector coverage
and unknown-secret rejection remain active. Scanner CLI behavior was checked
against the primary [detect-secrets documentation](https://github.com/yelp/detect-secrets/blob/master/README.md).

No original result, PI approval, usability rating or publication selection is
inferred from these software checks.
