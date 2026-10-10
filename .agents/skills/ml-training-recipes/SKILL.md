---
name: ml-training-recipes
description: Use by sim_engineer for reproducible training configuration and diagnostics in approved wireless experiments.
---

# ml-training-recipes

Operational adaptation of reviewed Orchestra ml-training-recipes (MIT in vendor).
Pin framework versions and datasets, save initial seeds/configs/checkpoints,
separate tuning data from test and log validation curves. Check NaNs, gradients,
constraint violations and multiple-seed variance. Use conservative CPU settings
until actual accelerator inventory is known. No automatic cloud spend or GPU claim.
