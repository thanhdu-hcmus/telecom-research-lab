# P6 verification status

## Second canonical attempt: completed; INCONCLUSIVE

| Check | Actual result |
|---|---|
| Native verification | PASS: eight checks and seven prediction items |
| Supplement | CHECKED_WITH_DECLARED_UNRESOLVED |
| Combined assessment | INCONCLUSIVE; not eligible for G6 request |
| Coverage | 145 jobs, 4,718,692 rows; 4,708 base and 1,160 tighter replays |
| Recorded errors | Zero |
| Precision failures | None |
| Integrity | All 19 reviewed source bindings and 51 locked inputs unchanged |

The supplement finished on 2026-10-13 at 14:03 UTC. Its completed computation
is retained in analysis/supplement/completed-attempt-02/closure-receipt.json,
with exact links and hashes for the native, supplement and assessment receipts.
The enforced fifth source review returned READY with zero findings; its source
correction was applied before this fresh canonical attempt. The accepted-source
unit run has 133 passing cases; the corresponding framework run has 97 passes.
These test results do not establish scientific acceptance.

## Remaining numerical uncertainty

Five stored deterministic rows remain unresolved. Twenty base-oracle checks
cover four stress cases repeated five times. The combined oracle uncertainty
sum of 55 repeats categories; it is not a count of distinct rows. No unresolved
base check was selected for canonical tighter replay. Extra author diagnostics
using the existing tighter policy returned ten feasible and ten unresolved
results; exact checks validate the ten feasible witnesses, without changing
canonical labels or acceptance.

The author fractional-boundary certificate explains the exact sqrt(2)-1
singleton. It has not upgraded the verifier's unresolved labels. See
analysis/supplement/attempt2-native-checkpoint and
analysis/supplement/oracle-uncertainty-author-diagnostic.

## Claim lineage and independent review

The current run generated 39 executable conditional recipes: 36 are COMPUTED
and three are INCONCLUSIVE. Computation receipts are not accepted manuscript
claims. Nine native arithmetic examples remain provisional and unregistered.
Independent numerical-results review and resolution or scientific treatment
of the retained uncertainty remain required before G6 can be requested.
A local artifact-selection plan is retained in analysis/numerical-review-preparation.
No numerical-results packet has been transmitted. G6/G7 remain PI-only.

## First attempt: failed; preserved

The first full attempt completed the same 145 jobs and 4,718,692 rows. Native
verification passed, while the supplement and combined assessment failed with
2,968 diagnostic crossing errors (2,964 upper and four lower). The reviewed
round-five correction removes those recorded errors in the fresh full attempt.
Original outputs and failure evidence remain in
analysis/supplement/completed-attempt-01 and
analysis/supplement/native-output-archive-attempt1.

M11 still requires accepted scientific results, the P7 manuscript/review/export
and actual PI G6/G7 decisions. M12 remains unstarted.

## First numerical review packet prepared locally

The complete bundle is too large for the observed review context. The first
scoped packet contains 32 artifacts and 517,502 bytes, covering all 100
deterministic raw rows, certificate handling and methodology. It excludes
author narratives and previous review/test verdicts. Two derived report views
are explicitly labelled and checked against their original full reports.
Monte Carlo numerical acceptance remains outside this first review. See
analysis/numerical-review-01-deterministic-payload.json. No transmission has
occurred; separate authorization is pending.
