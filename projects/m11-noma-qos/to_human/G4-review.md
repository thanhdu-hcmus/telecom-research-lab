# G4 review: M11 exact model

## Decision requested

Accept the idea-01 mathematical specification and its explicit limits as the
model for the approved two-user NOMA/QoS versus matched equal-time OMA dry run.
Recommendation: approve G4 after reviewing the evidence below.

G3 was approved by the PI in commit cb4061a, selecting idea-01 and rating the
report usable. Your later “Approved” authorized the bounded external P4 review,
recorded in provenance session0014. That permission is separate from G4.
The lab-orchestrator skill and repository AGENTS.md reserve G4 for the PI;
P5 protocol design starts only after that recorded decision.

## What is ready

- A model specification with signal equations, both weak-message decoding sites,
  exact QoS bounds, optimizer and curvature proofs, all zero/equal-gain branches,
  matched OMA resource accounting and complete feasibility denominators.
- Seven cited assumptions, seven falsifiable predictions and 40 notation entries.
- Thirteen passing bounded symbolic checks, with their exact input digest.
- Two actual independent model_critic rounds. Both recommend ready and report
  zero actionable findings. Each answers eleven telecom checklist items and six
  rigor dimensions. The final handoff reviews the current artifact revisions.
- Verified separate read-only roots/children, no reviewer tools/network calls,
  unchanged supplied files and parity with actual named-child final messages.
- A proposed structurally independent scalar oracle, not an implementation.

The parent clarified SINR/rate terminology in A4 and explicit zero-branch output
assignments between rounds; the final reviewer saw those revisions. First-round
outputs and original bytes remain available. The initial external launch was
rejected before process start, then the PI authorized the bounded action. A local
handoff validator initially counted string characters instead of summary lines;
it was corrected without changing the actual six-line reviewer summary.

## Mathematical conclusions to review

Let A=P*g_w and B=P*g_s be full-power received SNRs, with 0<=A<=B;
a is the strong-user fraction and T_i=2^(q_i)-1.

| Claim | Exact regime and limit |
| --- | --- |
| Weak rate log2((1+A)/(1+a*A)); strong rate log2(1+a*B) | Ideal ordered scalar Gaussian model, perfect CSI and SIC; both weak decoding sites checked |
| Feasible interval [L,U], with L=T_s/B and U=min(1,(A-T_w)/(A*(1+T_w))) | A>0; interval empty if L>U. Zero received SNRs use explicit separate branches, without division by zero |
| U maximizes the sum | Unique when B>A; equal SNRs give a constant sum over the feasible interval. A singleton is feasible |
| OMA feasibility implies NOMA feasibility | Equal-time OMA, full P in each active half-slot, identical block/channels/targets/bandwidth; both schemes spend P*tau energy |
| Optimal NOMA sum >= OMA sum on both-feasible blocks | Strict when B>A, equality when A=B. This is a derived ideal-model theorem, not a measured gain or individual-rate dominance claim |
| All joint feasibility counts retained | Exact OMA-only count is predicted zero. Any numerical contradiction is retained for diagnosis; paired summaries use the both-feasible denominator and stay undefined when it is zero |

The target objective, full split range and baseline remain those approved at G1/G3.
No paper-specific half-power ordering, stability margin, distribution, different
OMA scheduler or original novelty claim is introduced.

## Evidence to spot-check

- [Model specification](../model/model-spec.tex): QoS interval, zero branches,
  derivative signs, fairness witness and strict/equality proof.
- [Algorithm](../model/algorithm.md): complete output/status branches and the
  proposed independent oracle's data-flow restrictions.
- [Assumptions](../model/assumptions.yaml), [predictions](../model/predictions.yaml)
  and [notation](../model/notation.yaml): scope and falsification conditions.
- [Source map](../model/source-map.md): six grounded manuscripts, cached pages and
  transfer restrictions; final-journal pagination is not substituted for PDF pages.
- [Symbolic checks](../model/checks.yaml) and [results](../model/check-results.json).
- [Final critique](../model/critique.yaml) and [response](../model/response.md).
- `ara/staging/P4-critic-round-01.json`, `P4-critic-round-01-acceptance.json`,
  `P4-critic-acceptance.json`, `P4-parent-clarifications.json`, `P4-final-checks.json`
  and `P4-review-effort.json`: actual reviews, permissions, preserved bytes and effort.
- [Generated G4 report](G4-report.md): final artifact bindings and automated checks.

## Limits and work left for P5

The reviewer used supplied artifacts and published extracted pages, without
independently authenticating original PDFs, bibliographic metadata, stored hashes
or historical gate decisions. Parent byte/binding checks are separate. Damaged
source equations are not used as proof. Bounded symbolic PASS is not complete
validation of every inequality, domain branch or future numerical implementation.

This model excludes imperfect CSI/SIC, finite-block coding, finite modulation,
hardware and feedback overhead, optimized OMA scheduling and deployment geometry.
It establishes no population outage probability without a sampling model.

The independent scalar oracle, numerical certificates, unresolved-numerical
statuses, tolerances, precision, QoS/SNR grids, fading distribution, seeds, sample
counts, stopping rules, uncertainty reporting and workloads remain P5 proposals.
Finite grids/root bracketing alone cannot universally decide arbitrary exact-real
singleton equality. Reviewer-suggested examples are proposed cases, not executed
checks or locked protocol choices. No simulations or measured M11 results exist.
M11 remains in progress and M12 remains unstarted.

## PI action

If you accept the model and find the report usable, run from the repository root:

```powershell
.\.venv\Scripts\lab.exe gate approve G4 --project m11-noma-qos --note "P4 model and evidence reviewed; ideal-model limits accepted; G4 report usable" --json
```

Enter the CLI's fresh confirmation yourself. Use your actual usability judgment
in the note. If revisions are needed, use `lab gate revise G4` with an explanatory
note. Approve only after the generated G4 report shows passing checks.
