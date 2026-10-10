---
name: baseline-reproduction
description: Use by sim_engineer in approved P5 to pin, scan, review and reproduce paper-linked baseline code.
---

# baseline-reproduction

Read candidate evidence and config/baselines.yaml. Clone a full immutable GitHub
commit through lab baseline clone into ignored external/. Scan and manually
review all source, dependencies, license and data; a clean scan is not clearance.
Record reviewed file hashes before lab baseline env creates an isolated uv venv.
Never run unreviewed downloads. MATLAB execution uses a function with an onCleanup
path restoration and explicit addpath for the reviewed source only.
Reproduce the named paper figure/table. Save reference and actual curves, pinned
code, environment, seeds and run manifest. Compare declared units using the
agreement settings in config/baselines.yaml (defaults: <=0.5 dB absolute or <=5%
relative plus same trend/order). Pass the project policy to lab.baseline.overlay.
Only then score: venue/citation tiers exclusive, official link, license and
maintenance/self-contained evidence. Reproduction and the configured minimum
score (default 3) are mandatory; licence permission remains mandatory even if
licence points are set to zero;
tutorials, unverifiable paper links or disallowed data are always rejected.
