---
name: simulation-engineering
description: Use by sim_engineer in approved P5 to lock protocols, implement validated physics and run reproducible fair comparisons.
---

# simulation-engineering

Require G4 before any experiment. Read model, predictions and findings. Specify
sim/protocol.md/yaml with scenarios/seeds, metrics, params, equal power/bandwidth/
CSI/QoS, common channels, trial CI/event policy, ablations and locked code inputs.
Read [Monte Carlo standards](references/monte-carlo.md) and
[MATLAB bridge](references/matlab-bridge.md). Commit protocol and all inputs first;
lab sim lock refuses dirty inputs and verifies real Git ancestry. Run physics
tests before lab sim run, then status/collect. Save raw draws, metrics, runtimes,
environment and checksum manifests. Resume only verified complete seed jobs.
A better metric or changed baseline mid-run requires lab deviation open with
what/why/proposed_change/impact, then PI decision and a fresh protocol review.
Never edit a locked protocol or approve a gate. Bug fixes affecting locked source
require a recorded new protocol version; keep old runs and explain the change.
