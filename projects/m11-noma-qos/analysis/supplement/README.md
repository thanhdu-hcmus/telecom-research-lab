# P6 independent supplemental checker â€” prepared only

This directory contains independently written calculations from the approved
model/protocol and raw-output schema. Preparation and isolated unit tests do not
constitute verification of the canonical scientific results. Full execution
must follow an enforced independent artifact-only source review that binds all 19 approved source files. Round 1 requested revisions; round 2 is reviewing the revised source. No full canonical verification has run.

Run from the repository root in the existing pinned environment:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
.venv/Scripts/python.exe projects/m11-noma-qos/analysis/supplement/run_unit_tests.py
.venv/Scripts/python.exe projects/m11-noma-qos/analysis/supplement/checker.py --prepare
# After an enforced source-ready receipt:
.venv/Scripts/python.exe projects/m11-noma-qos/analysis/supplement/checker.py --native
.venv/Scripts/python.exe projects/m11-noma-qos/analysis/supplement/checker.py --execute
```

## Components

- `independent.py`: received powers and original SINRs, both weak decoding sites,
  log1p rates, matched half-block OMA; full-domain monotone constraint brackets,
  exact Fraction certificates for integer QoS; independent OMA boundary rules;
  raw fields, masks, residuals, paired differences, 101-point grid and a=.25;
  streaming Welford sample variance and Student-t CIs, exact binomial intervals,
  published OMA exp/E1 equations.
- `replay.py`: **shared pinned oracle replay**, separately labelled. It imports
  only the approved oracle.py module; it is not a third independent optimizer.
  Every stored field/certificate/status is compared with replay, with input/row
  binding and mandatory tighter checks. Synthetic test solvers are test-only.
- `checker.py`: production path/hash/manifest guards; exact inventory of 145 jobs,
  protocol parameters, deterministic 20-case table repeated five times, seeded
  PCG64/SeedSequence([seed,0]) gains, positional metrics alignment, per-job ledger,
  setting summaries and six OMA references.
- `test_supplement.py`, `run_unit_tests.py`: isolated in-memory and disposable
  corruption tests, log and actual machine-readable test receipt.
- `preparation.json`: source and artifact/output hash bindings plus the unit
  result; explicitly records that canonical execution has not occurred.

## Independent adjudication

NOMA feasibility uses predicates from original constraints over the entire
[0,1] domain. Each decreasing weak constraint and increasing strong constraint
is bracketed with cap 96 and split resolution 1e-12. For integer QoS, original
SINR constraints have positive denominators, so multiplying them out yields
affine Fraction residuals. After original-domain bracketing, exact interpolation
between residual values at 0 and 1 supplies a root; its bracket membership and
original residual are checked. This certifies zero, equal-gain, singleton and
very narrow integer cases without using the author's L/U classifier.

For noninteger QoS, disjoint bracket/rate separation can certify numerical
infeasibility; an inner overlap wider than SPLIT supplies numerical feasibility. An uncertified narrower overlap, overlapping
root brackets and rate-band ambiguity remain unresolved. The independent
ambiguity ledger is separate from stored categories, including when the author
reported a resolved row that this checker cannot settle. Diagnostic recorded
interval crossings are checked independently as original affine identities;
they are not the feasibility decision.

The numerical optimal sum is checked at the independently reconstructed weak
boundary using the approved monotonicity law, and candidate original constraints
are checked separately. This is not a new independent optimizer certificate.
Grid ties admit feasible maximizing entries within the existing objective
tolerance; grid misses do not adjudicate full-domain infeasibility.

OMA computes whole-block half rates and uses the declared 1e-9 ambiguity band.
Integer-target boundary decisions use exact Fraction received SNRs versus
2^(2q)-1; noninteger boundary cases remain unresolved. Both-zero-QoS regimes
have an elementary feasibility reason. An empirical zero-event observation
still has its exact two-sided binomial upper bound.

## Execution, outputs and limits

The CLI checks the native P6 phase and lock, calls native verify_manifest exactly
once per job, and uses native manifest_output/within/sha256 utilities. It neither
caches nor bypasses those guards. Preparation hashes approved artifact bytes and
checksum-bound outputs; it does not run native scientific verification.

One job's two-column seeded gains, first 32/100 replay rows, and fixed 101-element grid arrays are retained.
Wide CSVs stream row by row; all 4.7 million wide rows are never retained.
Defaults limit each job to 3600 seconds, total execution to 86400 seconds and
Python traced allocation peak to 1024 MiB. Traced allocations are not a complete
OS resident-memory measurement. Runtime and traced memory appear in the report.
Budget exhaustion or an exception is INCOMPLETE with an execution report.
No timing estimate is a measured canonical runtime.

Execution creates a unique runs/<timestamp>-<uuid>-supplement directory for execution.jsonl, ambiguities.jsonl, execution-report.json and claim-lineage.json. Native attempts, combined assessments and standalone lineage runs also use separate unique receipt directories. Error counts cover all occurrences; up to 2000 detailed
errors are retained to bound memory. Inputs and supplemental sources are bound
before execution and rechecked afterward, including on failure. JSON forbids
NaN in reports; CSV NaN is allowed only where an undefined value is expected.

Full coverage requires 145 jobs, 4,718,692 rows, 4,708 base oracle replays and
1,160 tighter replays (first eight of every job; tolerances divided by ten,
root/optimizer caps 96/256). Empty/missing/extra/duplicate work cannot pass.
Rate fields and paired negative decisions use the existing 1e-9 tolerance;
objective fields use 1e-7, splits
1e-12; binding/row identity and discrete counts/statuses are exact.

Setting CIs use independently recomputed both-feasible rates with n=n11.
Unresolved rows remain adjacent to resolved denominators. Deterministic repeats
receive no statistical CI. n11=0 has undefined means; n<2 has undefined CIs.
Zero means have no relative precision claim. The 100 observed-event rule is
reported separately from empirical zero-event bounds. The six unfiltered OMA
reference means/CIs use all independent zero-QoS draws and the published
equations from protocol.md, with <=5% relative agreement, ordering and trend.

A run with unsupported independent predicates for stored resolved rows is
INCOMPLETE. When all comparable fields agree and only the declared unresolved
policy remains, the status is CHECKED_WITH_DECLARED_UNRESOLVED. The preparation
inventory records the five stored unresolved deterministic rows explicitly.
Neither status establishes those rows mathematically or constitutes a full
scientific PASS. Comparison with the retained author statistics uses its stored n11 mask, checked against independent original-constraint categories. Executable claim lineage uses a separate independently resolved both-feasible mask, with every manifest and raw-file digest bound. Unsupported stored predicates prevent completion. The analysis-only combined assessment retains native receipts and emits scoped PASS, FAIL or INCONCLUSIVE items; any retained uncertainty or insufficient precision prevents PASS.

Context7 documentation was fetched for NumPy Generator/PCG64/SeedSequence and
SciPy Student-t/beta quantiles before library-specific implementation. The original independent calculations excluded author narratives and analytic, experiment and aggregate source. The bounded external source review includes the pinned native verifier and framework entry point to assess interoperability. The parent uses the resulting findings for analysis-only repairs.

Raw SINR differences are dimensionless diagnostics; comparisons use their
implied log1p rates and the declared rate tolerance. Event counts, denominators and point estimates remain exact. Equivalent exact-interval implementations use a dimensionless engineering roundoff allowance of 64 ULPs at one for interval endpoints. This does not change scientific or solver tolerances. Relative CI values must satisfy their reported
mean/halfwidth identity and their implied halfwidth in rate units. Finite
attempted candidates are checked even when the accepted optimum is undefined.

The synthetic timing receipt is an explicitly bounded ordinary-row estimate,
including the large tracing overhead; it excludes IO, native guards, hashing and
shared replay. Runtime-budget exhaustion remains INCOMPLETE. Initial failed
test/lint receipts and the initial timing estimate are preserved. No readiness
for a full canonical run is claimed.

## Source-review repairs and retained evidence

The current isolated suite has 87 tests and seven subtests (94 JUnit cases), with
no failures or skips. Its unique unit-runs directory records source hashes and
full outputs. These checks include the already approved 24 illustrative rows;
they establish bounded schema interoperability only. Original source, receipts,
failed tests, review findings and repair evidence remain in source-review-01.
The earlier preparation.json is an immutable historical preparation checkpoint.
It does not describe the newly revised code or establish current readiness.

Candidate diagnostic flags are checked against verified serialized rates. Their
independently recomputed predicates are checked separately; only a discrepancy
within 64 ULPs of each rate can be reported as binary64 diagnostic roundoff.
Original constraint adjudication and the declared tolerances remain unchanged.
Invalid flag semantics and material disagreement fail. Grid membership uses an
integer index plus the approved split tolerance, then reevaluates the recorded
split. Selected endpoint and weak-target activation are checked even for equal
gains. Positive product underflow is unsupported, never exact zero capacity.

Shared replay compares analytic, base, tighter and independent objectives and
classifications. Missing feasible optimality and unresolved classifications are
explicit; optimality is not applicable on a certified infeasible case. Those
counts are carried into the combined assessment. None of these numerical checks
establishes a universal real-input proof.

Standalone lineage recipes are executable with --lineage-recipe. They enforce
the independent endpoint and original constraints, stream all bound manifests,
retain null for an empty denominator, and leave a unique receipt on failure.
An output marked COMPUTED is a computation receipt, not scientific acceptance.
Lineage from a failed audit is marked UNVERIFIED_DUE_TO_ERRORS. The --assess
operation writes a unique combined-assessment.json and combined-verification.yaml.
Native scientific verification continues through the unmodified lab API and its
ordinary integrity guards. Budget checks are cooperative, including around
hashing and replay; individual native calls may overshoot a checkpoint.
