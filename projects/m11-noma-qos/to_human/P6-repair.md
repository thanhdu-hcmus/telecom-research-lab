# P6 framework repair — PI action needed

## What happened

Your G5 approval is recorded in commit `b289a06` (2026-10-11). Native P6
phase start passed. Its verifier preflight then stopped before executing any
scientific verifier: the approved protocol declares `verifier`, while the
framework reads only `verification_entrypoint`. This is an implementation bug.
No P6 numerical verification or G6 approval is claimed.

## Concrete repair

- Accept either declaration; reject conflicting declarations.
- Keep the existing distinct-script, pinned-input and simulator-import guards.
- Raise the bounded verifier execution budget from 600 to 3600 seconds. The P5
  integrity-status receipt spans about 747 seconds by filesystem timestamps;
  that is approximate timing evidence. No P6 timeout has occurred. This proposal
  changes execution budget only, not solver tolerances or numerical settings.

Review the proposed patch in `ara/staging/P6-framework-fix.patch` and tests in
`ara/staging/P6-entrypoint-tests.py`. The patch was applied only to an isolated
copy under `.cache/p6-compatibility-01`.

## Completed checks

- Original-code reproduction: 2 failing / 5 passing targeted cases; with the
  prospective timeout assertion, 4 failing / 3 passing cases.
- Patched isolated copy: 7 targeted cases pass; final formatted tests also pass.
- Full isolated regression: **97 passed**, zero failures/errors/skips.
- Ruff passes for the isolated framework and final proposed tests.
- **All 51 canonical locked inputs remain unchanged.** Original results and
  approved artifacts have not been edited. Raw JUnit logs remain local.
- No external reviewer was launched. Scientific independence and recomputation
  remain P6 work after the native entrypoint is repaired.

Evidence: `ara/staging/P6-fix-preparation.json` and
`docs/evidence/m11-p6-entrypoint-preflight.json` (repository root).

## Required PI action

Repository `AGENTS.md` rules 1 and 4 and the `lab-orchestrator` skill reserve
scientific gate rewinds and locked-protocol changes to the PI. The affected
framework file is itself a locked protocol input, and `lab sim relock` requires
P5. I therefore need an actual canonical rewind, even though the proposed repair
is already tested and the scientific assumptions are unchanged.

From `D:\02_EDUCATION\THESIS\telecom-research-lab`, run:

```powershell
.\.venv\Scripts\lab.exe gate rewind P5 --project m11-noma-qos --note "Repair verifier entrypoint compatibility and execution budget; preserve approved numerical evidence" --json
```

Respond to the command's PI confirmation prompt yourself. Rewind archives the
existing `sim`, `results`, `analysis` and `paper` directories; it does not delete
the data. G1–G4 remain approved; G5–G7 are invalidated for fresh review.

After the rewind I can apply the prepared fix, review verifier coverage, restore
unchanged simulation sources, commit and create a fresh lock, rerun the fixed
manifest jobs, and prepare a new G5 packet. Independent P6 verification follows
that renewed G5 decision. Earlier G5-pending notes are historical; its current
canonical status remains approved until you perform the rewind.
