# P5 sim_engineer brief

G4 is canonically approved in PI commit 08808d8, model accepted and report usable.
Phase start P5 succeeded. Use .codex/agents/sim_engineer.toml and applicable
simulation-engineering and baseline-reproduction skills; DL is outside this scope.
Read AGENTS.md, research-state.yaml, findings.md, model/*, scope.yaml,
ideas/idea-01.yaml, lab/simulation.py and lab/verification.py (custom entry contract).

## Outputs and scope

Write only projects/m11-noma-qos/sim/src/ and sim/tests/ plus
ara/staging/P5-engineer-design.md. No commits, locks, simulations, network installs,
gate decisions, subagents, or changes to approved artifacts. Parent writes protocol.
User requested implementation of the original plan; P5 section explicitly requires
unit/physics tests of simulation functions. Prepare these tests, parent runs them.

Implement Python analytic.py vectorized closed form from the approved P4 model,
with input validation, stable log1p/expm1, explicit zero/equal/singleton branches,
infeasible optimal rates undefined. No half-power constraints. Return full QoS
ledger and original direct SINRs/constraint residuals. Binary64 close-boundary
classification must be flagged rather than silently relaxed or clamped.

Implement oracle.py separately: original inputs and original SINRs/full [0,1],
no imports from analytic.py, no copied L/U/endpoint rule, no derivative-sign
optimizer. Root bracketing of original rate constraints is permitted, followed
by structurally independent bounded scalar optimization. Explain precisely what
is certified and what is merely solver agreement. Use exact rational checks for
integer-QoS deterministic singletons or retain unresolved status. A finite grid
cannot certify infeasibility. Avoid an expensive unconverged brute-force scheme;
record tolerances/caps and return unresolved on failure. A conservative monotone
constraint bracket and concavity-based objective upper bound from direct rate
secants is permitted (approved P4 concavity, no derivative sign).

Prefer existing NumPy/SciPy and standard Python Decimal/Fraction; no added deps.
Use Context7 for new library API syntax. Parent already fetched official NumPy
Generator(PCG64(SeedSequence([seed, stream_id]))) and scipy.stats.t.ppf docs.
Keep callable APIs simple for parent entrypoint: analytic.solve(P, gw, gs, qw, qs)
and oracle.solve(P, gw, gs, qw, qs, **tolerances), direct rates independent.

Tests should cover zero power/gains/targets, equal gains, infeasible cases, interior
and endpoint, exact singleton A=3 B=9 qw=1 qs=2 at a=1/3, invalid inputs,
near-boundary unresolved, direct original constraints and oracle agreement.
Use target rate tolerance 1e-9, split tolerance 1e-12, objective tolerance 1e-7
as proposed defaults, not permission to change mathematical feasibility.
Document stable domain limits, output fields and unresolved semantics.

Done: readable UTF-8 LF code/design, no scientific claims beyond model, <=15-line
handoff with paths, interfaces and unresolved issues. Do not execute simulations.
