---
name: results-verification
description: Use by results_verifier in approved P6 to independently recompute metrics, test predictions and build numeric claim lineage.
---

# results-verification

Read artifacts and raw manifest outputs only, not author reasoning. Write only
analysis/. Recompute metrics with an independent implementation; never call the
simulator's metric function. Check units/path loss/noise, constraints/convergence,
common draws/equal power/CSI/QoS, baseline ordering, sensitivities and ablations.
Test approved predictions with declared regimes/tolerances. Averages need target
CI halfwidth; outage needs >=100 observed events and exact/Wilson CIs. Zero events
means an upper bound. Save independent checks, input hashes and verification items.
Triage failures as implementation-bug, theory-error, approximation-gap or
statistical-noise. Inconclusive is not PASS. Every numeric claim must name a valid
manifest output and executable JSON computation, with intended manuscript usage.
Use lab verify and lab.verification.evaluate_claim; never invent a claim value.
