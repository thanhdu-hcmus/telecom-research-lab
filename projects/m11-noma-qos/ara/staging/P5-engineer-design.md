# M11 P5 engineer implementation handoff

This implements the G4-approved model inside the named P5 paths. No protocol,
approved model, gate decision, commit, lock, experiment, or baseline acceptance
was changed. Tests are prepared for the parent to execute; no test pass or
simulation result is claimed here. No third-party baseline code is imported.
The baseline-reproduction skill applies to any later paper figure reproduction,
not to an unverified downloaded implementation. DL skills are outside this model.

## Interfaces

- `sim/src/analytic.py`: `solve(P, gw, gs, qw, qs,
  rate_tolerance=1e-9, split_tolerance=1e-12)` broadcasts all five inputs.
  All returned fields are NumPy arrays of the common shape. Scalar inputs
  return zero-dimensional arrays; use `.item()` for scalar serialization.
  `direct_rates(P, gw, gs, a)` returns original three SINRs and site/rate fields.
- `sim/src/oracle.py`: independent scalar `solve(P, gw, gs, qw, qs,
  rate_tolerance=1e-9, split_tolerance=1e-12, objective_tolerance=1e-7,
  max_root_iterations=96, max_optimizer_iterations=256)` returns Python scalars.
  Its `direct_rates(P, gw, gs, a)` is separately implemented, never imported
  from the closed form. It neither accepts analytic endpoints nor copies their
  formulas or the derivative sign optimizer.
- `sim/tests/test_noma_physics.py`: deterministic pytest checks, no sampling
  or simulations. Run through the project's existing Python environment.

## Output semantics

| Field | Meaning |
| --- | --- |
| `status` | `feasible`, `infeasible`, or `unresolved`; no silently relaxed QoS |
| `feasible` | 1, 0, or NaN respectively; NaN is not a false indicator |
| `a_star`, `rw`, `rs`, `sum_rate` | Numerical approximation to the constrained optimum; undefined for infeasible/unresolved |
| `candidate_a`, `candidate_*` | Retained attempted candidate and original direct-SINR diagnostics if available, including failed attempts |
| `residual_w`, `residual_s`, `sic_residual` | Unrounded original rate differences, retaining negative values |
| `exact_split` | Fraction string when a relevant rational witness/endpoint is certified; a float is only an approximation to that split |
| `singleton` | True only when singleton established by the relevant certificate |
| `certificate` (analytic), `feasibility_certificate` (oracle) | Separates exact rational/zero evidence from ordinary binary64 numerical evaluations |

The analytic ledger additionally supplies `A`, `B`, `interval_lower/upper`,
`boundary_flag`, `numeric_domain`, `candidate_violation`, `optimizer_unique`,
`nonunique`, `candidate_constraints_pass`, `candidate_within_rate_tolerance`,
`oma_status`, `oma_feasible`, `oma_certificate`, `oma_boundary_flag`,
`oma_rw/rs/sum`, `oma_residual_w/s`, `category`, and `paired_difference`.
Its `rw_site`, `cw_at_s`, `gamma_ww/ws/ss` are the three original site quantities.
`category` is n00/n01/n10/n11 only when both indicators resolve; otherwise
`unresolved`. Parent aggregation must retain unresolved counts and their original
total denominator separately, never drop them or force them into a binary cell.
`paired_difference` is NaN outside n11. OMA reference rates remain labeled
unconstrained values even if its status is infeasible; they are not a constrained
OMA optimum or accepted paired observation.

The oracle additionally supplies `inner_lower/upper`, `outer_lower/upper`,
`root_iterations` (sum of both bracket searches), `optimizer_iterations`,
`optimizer_evaluations`, `objective_upper_bound`, `objective_gap_bound`,
`optimality_status`, `reason`, and the actual tolerance/cap settings.
It reports independent unfiltered `oma_rw/rs/sum`, but its OMA feasibility
classification is deliberately left to a separate verification implementation.

## Closed form and stable execution domain

Inputs must be finite, nonnegative, with gw <= gs; invalid domain raises
ValueError. Nonfinite or underflowed positive received products return unresolved.
Rates use log1p of original SINRs, with min of both weak decoding capacities.
The upper endpoint uses
`exp(-qw*ln2) + expm1(-qw*ln2)/A`, algebraically equal to the approved expression
and avoiding the large `A*(1+Tw)` denominator. Strong targets use expm1.
Exponent overflow is not clamped into a feasible value: a capacity-separated
large target is infeasible. Underflowed nonzero target transforms are unresolved.
The implementation performs ordinary binary64 computation, not universal
arbitrary-precision arithmetic over every finite-real model input.

Zero cases are explicit. Zero targets deactivate their bound; all-zero SNR
chooses a=1 and returns zero rates. There is no half-power restriction. Equal
gains permit ties; uniqueness at equal gains requires a certified singleton.
No infeasible optimum is replaced by zero or by a clamped split.

For |L-U| <= 1e-12 the closed form withholds a classification unless both QoS
values are integers <= 1024, in which case Fraction uses exact representations
of original supplied binary64 P/gains and integer target powers. This establishes
mathematical feasibility/emptiness and possible equality, not exact feasibility
of the rounded floating candidate. Small direct residuals are always recorded;
the rate tolerance only diagnoses a failed numerical approximation. The
`candidate_constraints_pass` flag reports raw binary64 >=0 comparisons and may
be false for an approximation to a certified rational singleton.

OMA boundaries within 1e-9 of either positive target remain unresolved unless
integer-target exact Fraction capacity comparisons resolve them. Exact zero
gain with any positive target is infeasible even inside that band. Ordinary
`binary64-separated` classifications are numerical evidence, not rigorous
validated-numerics certificates.

## Independent oracle method and certificates

1. Start from original inputs and full [0,1]. Evaluate both original weak
   SINRs and strong post-SIC SINR. Integer targets <= 1024 use Fraction SINR
   inequalities, with no logarithm approximation in feasibility predicates.
   Other targets use separately evaluated original rates.
2. Independently bisect each monotone QoS predicate. Strong QoS is increasing;
   weak QoS is decreasing. Search until bracket width <= 1e-12 or 96 iterations.
   Keep outer (possible) and inner (satisfied) brackets. An exact comparison of
   disjoint rational outer brackets certifies emptiness. Numerical bracketing
   is labeled as such, and close/failed boundaries remain unresolved.
3. Near rational boundaries, try Fraction reconstruction at denominator caps
   1024, 65536, 1000000, and 2^32. Reconstruction is merely a witness search;
   the subsequent original SINR comparisons supply the exact certificate.
   Simultaneously active nondegenerate constraints establish a singleton;
   endpoint-only degenerate constraints are handled separately. An exact
   feasible witness without a resolved objective interval remains unresolved.
4. Apply SciPy bounded scalar minimization of negative direct sum rate to the
   independently bracketed inner interval. Evaluate both interval endpoints
   as well, because the bounded optimizer need not evaluate them. This choice
   follows objective values, with no derivative sign or analytic endpoint rule.
   A failed SciPy convergence flag remains unresolved even if a candidate exists.
5. Use direct objective secants around the best candidate to build the concave
   supporting-line envelope on the outer interval. For a concave function, its
   left secant at a center upper bounds slopes to the right, and its right
   secant lower bounds slopes to the left. The numerical bound covers the tiny
   excluded endpoint slivers, not only the optimizer's inner interval. Secant
   spacing is min(width/4, max(4*split_tolerance, width*1e-5)); the floating
   allowance is 256 ulps of the maximum sampled objective magnitude (at least1).
   Require numerical objective gap <= 1e-7 and direct residuals >= -1e-9.

The resulting `numerical-concavity-bound` is an explicit floating objective
diagnostic using the approved P4 concavity law. Its allowance is not a proved
interval-arithmetic error bound; it does not certify exact global optimality
for arbitrary real inputs. `exact-singleton` certifies uniqueness of the exact
feasible rational split; reported logarithmic rates still approximate its value.
These distinctions must survive the parent manifest and verification report.
Root and optimizer caps make cost bounded; unexpected cap hits, nonrepresentable
intervals, missing witnesses and excessive objective gaps retain unresolved
status and their diagnostics. No grid infers infeasibility.

## Deterministic correction and coverage

The supplied brief's A=3, B=6, qw=qs=1 example is **not a singleton**:
its interval is [1/6,1/3]. Parent corrected this before implementation.
The unequal-gain singleton is A=3, B=9, qw=1, qs=2 at a=1/3.
The equal-gain singleton is A=B=3, qw=qs=1 at a=1/3. Prepared tests assert
these distinctions and direct exact rational constraints. Other tests cover
zero power/gains/targets, tiny positive impossible zero-gain targets, endpoint
a=0/1, infeasibility, full split range, equal-gain ties, OMA factor1/2,
broadcasting, undefined optima/paired values, a noninteger narrow boundary,
root caps, overflow/underflow, invalid inputs, and independent oracle agreement.

## Documentation consulted

Context7 resolve/query selected the official NumPy and SciPy documentation.
The implementation follows NumPy's [broadcast_arrays](https://numpy.org/doc/stable/reference/generated/numpy.broadcast_arrays.html)
shape/view contract and [errstate](https://numpy.org/doc/stable/reference/routines.err.html)
local floating error handling, and SciPy's [bounded minimize_scalar](https://github.com/scipy/scipy/blob/main/doc/source/reference/optimize.minimize_scalar-bounded.rst)
method with explicit bounds, xatol and maxiter. No dependencies were installed.
