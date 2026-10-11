# P5 implementation prepared

G4 approval is verified in PI commit 08808d8; phase start P5 passed.

## Ready to execute

- [Protocol](../sim/protocol.md): 12 settings, 12 seeds each, 32,768 blocks
  per seed; 20 deterministic cases repeated five times. 145 manifest jobs.
- [Closed form](../sim/src/analytic.py) and [independent oracle](../sim/src/oracle.py):
  original SINRs, zero/equal/singleton cases, exact rational certificates where
  applicable, explicit numerical uncertainty and unresolved outputs.
- [Prepared physics checks](../sim/tests/test_noma_physics.py).
- [Experiment entrypoint](../sim/src/experiment.py), aggregation and OMA
  reference-overlay script, and a prepared P6 verifier for later independent review.
- [Engineer design](../ara/staging/P5-engineer-design.md) explains interfaces
  and numerical limitations. [Preparation receipt](../ara/staging/P5-preparation.json)
  records the actual specialist handoff and blocked test invocation.

Ruff static checks pass. The protocol schema and named inputs validate, and all
111 approved G1-G4 artifact hashes remain unchanged. These checks do not establish
numerical correctness. No protocol lock, test run, simulation, published-curve
agreement, or G5 decision is claimed. The P6 verifier is not independently reviewed
or accepted yet. Both source code and protocol are committed before results.

## Required explicit test request

Automatic approval review rejected the prepared pytest command before launch:
the developer instruction forbids running tests without an explicit user request.
The original implementation plan includes these checks, but automatic review
did not accept that as an explicit test-execution request. No alternate invocation
or indirect test run was used. No experiment starts before the physics prerequisite.

Please explicitly authorize: **Run the prepared M11 unit/physics tests, fix failures,
and continue the locked P5 simulations.** This is execution permission, not G5
approval. After successful checks, commit any fixes, lock, run/status/collect,
aggregate, report limitations, and request G5 for separate PI review.
