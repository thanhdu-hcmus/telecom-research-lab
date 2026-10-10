---
name: dl-for-wireless
description: Use by sim_engineer for approved P5 wireless learning experiments with explicit splits, budgets and generalization checks.
---

# dl-for-wireless

Choose learning only if the approved idea requires it. Record channel generation,
normalization and train/validation/test identifiers; split before fitting any
transform and prevent channel/user/scenario leakage. At least three training
seeds; record optimizer, hyperparameters, early stopping and equal tuning budget.
Compare against strong optimization/model-based baselines at equal power/CSI/QoS.
Test out-of-distribution channels, hardware/CSI imperfections and computational
cost. Verify feasibility after network predictions. Do not assume a GPU exists;
profile CPU feasibility first and file deviations for changed compute/metric scope.
