# Author census of remaining oracle uncertainty

The saved deterministic oracle has twenty unresolved base checks: four cases,
each repeated five times. The canonical tighter policy covers rows0-7; all
twenty unresolved rows occur later, so none has a canonical tighter replay.

| Case | Repeats | Base-oracle uncertainty | Exact author observation |
|---|---:|---|---|
| narrow-feasible | 5 | Feasible witness found; maximum unresolved in narrow interval | The stored exact witness1/3 equals the approved model's maximizing upper endpoint. |
| narrow-infeasible | 5 | Narrow domain lacks an oracle certificate | Exact rational lower bound exceeds the upper bound. |
| large-finite-snr | 5 | Numerical concavity gap exceeds tolerance | The stored candidate is exactly feasible and its model-derived rational objective-gap bound is below the declared tolerance. |
| fractional-boundary | 5 | Noninteger singleton lacks a direct oracle certificate | The separate author certificate derives sqrt(2)-1; saved labels stay unresolved. |

## Additional local replay

The same pinned oracle was called on these twenty saved inputs using the
existing tenfold tighter tolerances and unchanged96/256iteration caps.
These calls are extra author diagnostics. Canonical coverage remains
4,708base and1,160tighter calls. Actual returned statuses are in census.json.

## Large-SNR gap deduction

For A=P*g_w, B=2*A, q_w=q_s=1, the approved real-model optimum is
u=(A-1)/(2*A). For the stored exactly feasible candidate c, let
z=(A-1-2*c*A)/((1+A)*(1+2*c*A)). Direct substitution gives
F(u)-F(c)=log2(1+z). Since log(1+z)<=z and ln(2)>=1/2,
the nonnegative gap is at most2*z. Exact Fraction arithmetic checks
2*z against the actual declared objective tolerance for all five repeats.
The saved numerical oracle's loose gap bound still remains not-established.

These deductions explain uncertainty without changing runtime acceptance.
The canonical run, stored labels, source/model/protocol and PI gates remain
unchanged. Independent numerical-results review remains pending.

Extra tighter status counts: {"feasible": 10, "unresolved": 10}.

## Checked results of the extra tighter calls

| Case | Extra tighter results | Original constraints of accepted witnesses |
|---|---|---|
| narrow-feasible | 5 feasible | All three original SINR inequalities checked with exact rationals |
| narrow-infeasible | 5 unresolved | No accepted witness |
| large-finite-snr | 5 feasible | All three original SINR inequalities checked with exact rationals |
| fractional-boundary | 5 unresolved | No accepted witness |

All ten reported numerical objective-gap bounds are within the declared
tighter objective tolerance. These checks validate the extra diagnostic
witnesses, while the twenty canonical base checks retain their actual labels.
Ten extra checks remain unresolved. See extra-tighter-validation.json.
