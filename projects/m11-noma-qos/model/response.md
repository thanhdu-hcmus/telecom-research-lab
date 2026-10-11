# Response to independent model critique

## Actual independent reviews

Round 1 recommended ready and reported no actionable findings. Its original
review and acceptance proof are preserved in ara/staging/P4-critic-round-01.json
and P4-critic-round-01-acceptance.json. The reviewer examined all eleven telecom
checklist items and six rigor dimensions using only final artifacts and grounded
published pages, without tools, filesystem access or network calls.

The parent subsequently made two presentation clarifications: A4 now distinguishes
post-SIC SINR aB from rate log2(1+aB), and the pseudocode explicitly initializes
undefined outputs and assigns all zero-SNR rates, objective and non-uniqueness.
No equation, assumption, objective, constraint or baseline was changed. Original
bytes and before/after digests are retained in P4-parent-clarifications.json.

Round 2 independently reviewed the final artifact revisions and also recommended
ready with no findings. It received neither the author's reasoning nor the first
review. model/critique.yaml contains that actual final handoff. The parent checked
root/child read-only runtime, no reviewer tool calls, input immutability, complete
checklist/rigor responses and parity with the actual named child's final message.

## Limits retained

These are ideal scalar exact-real proofs, not practical receiver or deployment
validation. The bounded symbolic checks do not establish all inequalities or
branch handling independently. The reviewer did not independently authenticate
original PDFs, extraction fidelity, stored hashes or historical approvals.
The parent separately checks local bytes and approved artifact bindings.

The independent scalar oracle is a proposal, not an implementation. Finite
precision cannot universally certify arbitrary exact-real singleton equality
using a finite grid or root bracketing alone. A later P5 protocol must define
certificates or unresolved-numerical statuses, numerical tolerances, precision,
grids, sampling model, seeds, stopping rules and uncertainty reporting.
Reviewer-suggested examples remain proposed cases; they were not executed and
do not silently become protocol choices. No simulations or measured rate gains
exist. G4 is a separate PI decision; neither reviewer nor parent approved it.
