# P6 supplement implementation brief

## Status, scope and prerequisites

This is P5 engineering preparation addressing E01-E11 in
`P5-rerun-engineering-review.json`. It is not an independent verdict, a P6
artifact, execution evidence or scientific acceptance. At preparation, state
is P5 with G1-G4 approved, G5-G7 invalidated, and the fresh R2 protocol lock
recorded. The parent is running R2 jobs; no result from those jobs is asserted
here. P6 implementation/execution follows actual fresh G5 approval and native
P6 phase start. Preserve the physical protocol and every locked source byte.

Future supplements write only under project `analysis/`, with code, input
bindings, detailed receipts and logs retained. They must not import
`analytic.py`, `experiment.py`, `aggregate.py` or their metric helpers to produce
independent numerical values. Native manifest/path/hash utilities may be used
for integrity and inventory. Shared-reference replay may load the already
pinned `oracle.py` in an explicitly separate component. Record that distinction
in every combined report. Require fresh enforced independent artifact review
of native verifier plus supplements before a complete P6 acceptance claim.
This engineering brief and a native PASS cannot substitute for that review.

All scenario points, seeds, target values, methods, model constraints,
baselines, grid points, tolerances, confidence and event policy come from the
approved protocol. No additional scientific metric or sampling is proposed.
Coverage/error counts below are checks on already declared metrics and evidence.

## Implementation layout and bounded processing

Prepare future analysis components for: inventory/schema/sampling; independent
original-rate/feasibility/ledger checks; fixed/grid diagnostics; independently
rebuilt statistics/reference comparison; shared-reference replay; and combined
coverage/lineage. The exact filenames are routine implementation choices in
`analysis/`; write no implementation during this P5 preparation task.

Process one planned seed file or a chunk at a time. Maintain count/mean/centered
sum-of-squares accumulators per scenario and declared statistic, using stable
merge formulas. Keep row-specific diagnostics for every error/ambiguity, rather
than keeping all 4,718,592 MC rows in memory. A full seed channel array has only
32,768 pairs and can be retained for cross-setting comparison. Release each raw
structured table before loading the next one. Independently rebuilt summaries
may be small; raw evidence continues to reside at its manifest-bound location.
Measure runtime and peak memory, retain failures and partial logs, and report
any actual budget exhaustion. The prepared 3600-second native verifier budget
does not establish measured feasibility of native or supplemental execution.

## Exact raw file and field map

Use the actual fresh lock and planned manifest inventory, never an archived R1
path inferred from its name. Resolve project/library storage using each manifest.
CSV parsing must preserve empty strings for exact_split, NaN numeric markers,
integer row IDs, and explicit True/False booleans. Reject unknown boolean/status
tokens; `bool("False")` is not a valid parser. Require each column exactly once.

| File / fields | Type and meaning | Independent check |
| --- | --- | --- |
| `manifest.json`: scenario, seeds, params, language, protocol_hash/commit, input_hashes, outputs, runtime_s | Planned job and checksum lineage | Native immutable manifest validation; independently check full expected job inventory and bind raw rows to params |
| `channels.csv`: row | Integer position 0..trials-1 | Exact contiguous order and row count; align metrics.csv by position |
| P, gw, gs, qw, qs | Original binary64 model inputs | Finite/nonnegative, gw<=gs, manifest values or fixed case table; seeded gains |
| case_id | Present only in deterministic job | Exact ordered `cases.yaml` table repeated five times; IDs may repeat, row IDs cannot |
| A, B | Stored received SNR products | Independently form P*gw and P*gs; distinguish product overflow/underflow from invalid original inputs |
| status, feasible, certificate | NOMA status, 1/0/NaN indicator, evidence label | Allowed status tokens; independently classified feasibility and exact/numerical evidence type |
| interval_lower, interval_upper, boundary_flag | Analytic interval approximation and its ambiguity flag | Challenge interval membership/endpoints with own original constraints; do not use these fields to generate the independent bracket |
| numeric_domain, candidate_violation | Numerical execution-domain flag and failed candidate flag | Independently inspect intermediates and direct finite/rate diagnostics |
| a_star, candidate_a, exact_split | Optimum approximation, attempted candidate, optional rational endpoint/witness text | Split range, proper undefined masks, direct feasibility, independent exact Fraction witness check |
| singleton, optimizer_unique, nonunique | Optimizer-set flags | Committed deterministic singleton/tie/zero cases and exact boundary certificates; unknown rows do not assert flags |
| candidate_constraints_pass, candidate_within_rate_tolerance | Raw >=0 residual flag and diagnostic tolerance flag | Rebuild from unrounded own residuals; the latter does not change mathematical feasibility |
| gamma_ww, gamma_ws, gamma_ss | Original weak-at-weak, weak-at-strong, post-SIC SINRs at a_star | Own original signal/interference arithmetic |
| rw_site, cw_at_s, rw, rs, sum_rate | Weak capacity at weak site, weak capacity at strong site, minimum weak capacity, strong rate, total | Own log1p evaluation of original SINRs and minimum of weak sites |
| candidate_gamma_ww/ws/ss, candidate_rw_site, candidate_cw_at_s, candidate_rw, candidate_rs, candidate_sum_rate | Same eight quantities at candidate_a | Rebuild separately when attempted candidate is finite, including failed attempts |
| residual_w, residual_s, sic_residual | Candidate rw-qw, rs-qs, cw_at_s-rw_site | Own unrounded residuals at candidate_a; preserve small negatives |
| oma_status, oma_feasible, oma_certificate, oma_boundary_flag | OMA status/indicator/certificate/ambiguity | Independent individual-target comparisons and exact boundary adjudication |
| oma_rw, oma_rs, oma_sum, oma_residual_w, oma_residual_s | Unfiltered half-block full-P rates and target residuals | Own per-user OMA rates, total and target checks |
| category, paired_difference | n00/n01/n10/n11 or unresolved; difference defined on n11 only | Independently classified joint status and recomputed rate difference |
| fixed_feasible, fixed_sum | Fixed a=.25 diagnostic; undefined sum when failed | Own original rates and both QoS checks at .25 |
| grid_found_feasible, grid_sum, grid_a | Whether 101-point grid found a feasible split, its maximum and selected split | Own full declared grid evaluation, masks and objective values; misses remain misses |
| `metrics.csv`: feasible, oma_feasible, sum_rate, oma_sum, paired_difference, fixed_feasible, fixed_sum, grid_found_feasible, grid_sum, grid_a | Numeric projection of corresponding channels.csv columns | Exact positional/schema match and independently rebuilt values/masks |
| `ledger.json`: n00,n01,n10,n11,unresolved,N_total,N_resolved | Per-job ledger | Independent classification counts and all denominator identities |
| `oracle.json`: checks[].row, inputs, analytic_status, analytic_sum, oracle, optional tighter_oracle | Declared selected original/reference diagnostics | Raw-row binding and separate shared-reference replay below |
| `sampling.json` | Seed, trials, PCG64/SeedSequence entropy, law, stream and common-draw declarations | Compare against manifest/protocol and independently regenerated gains |
| `results/statistics.json` | Author-produced scenario and baseline summaries | Comparison target only; independently rebuild values and coverage |

The three `candidate_gamma_*` column names are individually
candidate_gamma_ww, candidate_gamma_ws, candidate_gamma_ss. The optimum rate
fields are all undefined when status is infeasible/unresolved. Candidate fields
and residuals may remain defined for an attempted candidate that later failed.
Unconstrained OMA rates remain defined even when OMA QoS fails. Exact_split may
remain as an evidence string on an unresolved numerical optimum. Preserve these
distinctions rather than imposing one universal NaN rule.

## Inventory, row coverage and resource/sampling contracts

1. Validate actual fresh protocol/lock ancestry and input hashes through the
   native deterministic machinery. Require exactly the Cartesian planned set
   of (scenario,seed) manifest pairs, no duplicate, missing or extra job. Every
   output is present and checksum/byte-size bound before reading. Bind code and
   helper dependency hashes used by the supplement, and recheck inputs before
   accepting its outputs. An empty inventory cannot pass via all().
2. Require the twelve MC settings and the one deterministic setting defined by
   protocol.yaml. MC seeds are the twelve listed values 11001..11012, 32,768
   rows each: 145 planned jobs, 4,718,592 MC scenario evaluations and 100 fixed
   rows. Derive expectations from the actual YAML and compare to these declared
   totals; do not silently accept a changed workload. Every MC row has exact
   scenario P/qw/qs; every fixed row matches the committed case table in order.
3. Regenerate the already declared PCG64 stream with SeedSequence([seed,0]),
   two unit-mean exponential gains per row, sorted weak/strong. Use a separate
   implementation of the draw construction, not channel_draws from the runner.
   This checks the same pinned generator/stream contract, not independence from
   NumPy's RNG algorithm. Require binary64 gain equality for the same pinned
   environment and exact reuse across every setting for a given seed/row.
   A reproducibility mismatch is diagnosed, not accepted with a new tolerance.
4. Distinct seed streams are within-setting independent replicates under the
   declared design. Cross-setting reuse is paired, so the twelve grids are not
   twelve independent realizations of the population. Fixed repeats are not
   independent observations. Noise/training/initialization streams are absent
   by model choice; add none.
5. Check normalized linear P against declared P_db using the existing conversion
   contract. Rate comparisons use identical gains, total P, unit noise/bandwidth,
   whole-block QoS and perfect CSI/ideal SIC. OMA uses full P in each half-block,
   so energy P and block bandwidth match NOMA; check each rate's factor1/2.
   No P/2, 2P, adaptive OMA scheduling or half-power NOMA constraint is introduced.

## Independent original-rate and feasibility recomputation

Write own rate evaluator from transmitted weak power P*(1-a), strong power P*a,
received interference and unit noise. Evaluate both weak decoding SINRs and
strong post-SIC SINR; use log1p/ln2, rw=min(two weak capacities), total=rw+rs.
Validate legal split range and finite expected fields before residual/max/CI
operations. Reject a NaN error explicitly; max(0,NaN) cannot serve as a receipt.

For each stored optimum and attempted candidate, independently rebuild the
field map above. Counts, row membership, statuses and schema are exact checks;
rate diagnostics use the declared 1e-9 rate-check policy, and comparisons
of constrained objective values use 1e-7. For SINR fields, retain raw differences
and compare their implied log1p decoding rates under the existing rate policy;
do not apply a bit/s/Hz tolerance directly to a dimensionless SINR. Dimensionless
or bitwise contracts must not acquire an invented relative tolerance. Raw
negative residuals remain visible even within the diagnostic tolerance.

### NOMA feasibility independent of stored endpoints

- Start at full [0,1], independently test original weak-site minimum and strong
  QoS, and bracket their monotone constraints with the declared cap96 per
  constraint and split tolerance1e-12. Keep inner satisfied and outer possible
  domains separately. Check endpoints and all zero branches before division.
- For integer targets supported by the pinned certificate path, form exact
  target SINRs and Fraction representations of original P/gains. Use original
  rational SINR predicates for bracketing and witness checks, never rounded A/B
  products or copied analytic L/U formulas. Validate stored rational witnesses
  exactly, while separately checking their floating approximations.
- Rational reconstruction from independent bracket samples may use the existing
  pinned reconstruction policy. If a reconstructed weak threshold has exactly
  active weak QoS and its strong residual is negative, monotonic constraints
  certify emptiness. Conversely, a direct rational witness certifies feasibility.
  Require the actual direct checks; reconstruction alone proves nothing. This
  can challenge the committed narrow integer cases without adding iterations,
  tolerance settings, target choices or an optimization rule.
- A numerical separated inner domain supplies finite numerical feasibility
  evidence. A separated empty outer domain supplies finite numerical emptiness
  evidence; record its binary64 limitations. Noninteger/uncertifiable overlapping
  brackets, failed caps and representability issues remain unresolved. A finite
  grid never proves emptiness. Do not turn a near equality into feasibility by
  applying a negative residual tolerance to the mathematical QoS condition.
- Compare resolved independent classification to stored status/indicator.
  If independent adjudication remains unresolved, keep that distinct from the
  stored status and record the incomplete check; do not overwrite the run or
  silently classify the instance. A feasible witness does not by itself certify
  the objective maximum. Independent row feasibility and objective-resolution
  status are separate diagnostics.

### Independent OMA and joint ledger

Compute each OMA rate as .5*log1p(P*g)/ln2 from original inputs. Compare both
individual targets using the protocol positive-target boundary band1e-9.
Exact zero gain with any positive target is infeasible regardless of that
band. Integer-target boundary cases use exact Fraction comparisons against
2^(2q)-1. Unsupported boundary cases remain unresolved. Keep unfiltered
OMA rates even outside its QoS set, and compare every stored OMA field.

Reconstruct joint category only when both independently adjudicated statuses
resolve, compare it to the stored indicators/status/category, and retain a
separate adjudication-ambiguity ledger where required. Independently rebuild
the stored-policy ledger as well, so incomplete independent adjudication is not
mistaken for a changed original denominator. Validate N_total=sum(four counts)
+N_unresolved and N_resolved=sum(four counts). Compare per-job ledger.json and
scenario aggregate counts, fractions, N values and paired denominator n11.
When resolved denominator is zero, fractions are undefined; when n11=0, paired
statistics are undefined. Do not discard unresolved instances from the report.

Compute paired difference only on independently verified both-feasible rows,
and compare the stored difference/mask. Check OMA-only and negative-paired
diagnostics and committed equal/zero/singleton cases. Distinguish tested finite
nonnegative/equality behavior from the P4 exact strict-inequality/curvature proof;
floating tiny differences cannot establish its universal strictness.

## Own fixed and 101-point grid diagnostics

Use the independent rate evaluator for a=.25 and exactly the protocol's 101
splits including 0 and 1. Reconstruct both target tests and per-method finite
rate masks. Match the runner's strict >= numerical candidate comparisons for
its stored fixed/grid receipts, while flagging close-boundary allocation
ambiguities separately under the existing diagnostic policy. Diagnostic
allocation checks do not alter the analytic mathematical-feasibility status.

Independently find the largest feasible grid sum. Check recorded grid_a belongs
to the declared grid, satisfies original constraints, and gives the recorded
maximum; objective ties may have different valid splits. For exact stored-rule
reproducibility, separately check the first-encountered strict-improvement tie
convention without treating that tie convention as a physical requirement.
A miss keeps grid_found_feasible=0 and undefined grid_a/grid_sum; it is not a
NOMA infeasibility certificate.

For fixed and grid, reconstruct found_feasible_count. On the declared joint
mask where analytic NOMA and that allocation are both feasible, rebuild paired_n,
mean_loss and minimum_loss from independently computed values, and compare
statistics.json. No overlap gives undefined losses, not zero; require scenario
coverage before evaluating any all() expression. Use the existing objective
tolerance for agreement/loss diagnostics, retaining raw losses and exceptions.

## Independently rebuilt statistical and OMA-reference inputs

Produce statistical inputs from independent rates and verified row masks,
then independently implement the declared statistical formulas rather than
calling average_ci/outage_ci from the author aggregation path. Reuse trusted
distribution quantile/special-function primitives if needed, with documentation
and versions recorded during actual implementation. No bootstrap, new confidence
level, extra seed, adaptive stopping or cross-setting significance claim is added.

- Within each MC setting, combine all verified n11 blocks; compute the two
  conditional sum means and mean paired difference, sample variance (n-1), and
  two-sided 95% Student-t interval using n=n11. Independently compare n, mean,
  variance-derived halfwidth, low/high and precision flags to aggregate records.
  Compare rate-valued summaries using the existing rate diagnostic tolerance;
  do not invent a new dimensionless threshold around the 1% precision policy.
  A numerically ambiguous threshold qualification remains inconclusive.
- n<2 gives undefined CI, n11=0 gives undefined mean, and deterministic rows
  receive no CI. Zero conditional means and deterministic ties use absolute
  residual reporting; do not assert relative precision from a zero denominator.
  A stable streaming accumulation may differ in the last bits from a full-array
  mean; record the raw differences and apply the existing diagnostic tolerance.
- Rebuild NOMA infeasibility=n00+n01, OMA infeasibility=n00+n10 and OMA-only=n01
  with denominator N_resolved and N_unresolved adjacent. Implement two-sided
  95% exact binomial intervals and compare count, estimate, bounds and event
  qualification. Fewer than100 events is inconclusive as an empirical outage
  estimate. Zero events gets an upper bound, never proof of zero. The exact
  zero-QoS feasible regime is a separate approved mathematical statement;
  it does not fabricate100 events or replace the empirical bound.
- Rebuild feasibility fractions and any intervals already declared for them.
  If independent adjudication leaves additional uncertainty, report incomplete
  population verification explicitly and do not manufacture a new full-ensemble
  confidence claim. Intervals are pointwise and no familywise guarantee is made.
- Recompute the declared six OMA-subset points at 0/10/20/30/40/50dB with all
  unfiltered zero-QoS draws. Independently evaluate the source-grounded published
  equations exp(2/P)E1(2/P)/(2ln2) and
  [2exp(1/P)E1(1/P)-exp(2/P)E1(2/P)]/(2ln2), along with the approved total-rate
  consistency expression. Rebuild each individual mean/CI, relative error,
  <=5% agreement, strong>weak ordering and increasing trend. Compare all points
  and summary flags to statistics.json and the numeric overlay source. This
  verifies only the already declared OMA subset, not Fair-NOMA allocation curves.

## Shared-reference replay: original and tighter oracle diagnostics

Keep this component labeled `shared pinned oracle replay`. It is independent
of the analytic closed form's code, but the P6 repetition is not a third
independent optimizer or a newly reproduced third-party implementation.

1. Require checked rows exactly 0..31 in each MC job and all0..99 fixed rows,
   with unique IDs and no outcome-based substitutions. Bind checked.inputs
   exactly to the five original raw fields, analytic_status to stored status,
   and analytic_sum/null to its documented raw sum mask/value. Reject wrong
   row/input order rather than comparing two unrelated sums.
2. Pass explicit manifest rate/split/objective tolerances and the already
   declared root96/optimizer256 caps to the pinned oracle. Compare saved versus
   replayed status, certificate kind, objective, constraints, gap diagnostics
   and declared cap/settings fields. Record actual caps/iterations and any
   failure or unresolved result. Exact singleton Fraction witnesses remain
   exact feasibility evidence; a numerical concavity bound remains numerical.
3. Require tighter_oracle exactly for the declared first eight rows of every
   job, including the fixed job: 145*8 planned tighter diagnostics. Replay the
   existing ten-times-tighter settings (rate1e-10, split1e-13, objective1e-8)
   with the same caps, not additional settings or selected replacement rows.
   Compare saved/replayed tighter statuses and finite values. Compare original
   versus tighter outcomes with explicit status-transition/null handling, not
   by skipping missing sums. Unresolved cases remain visible, and finite sum
   differences use the already declared objective-agreement policy.
4. The full declared reference coverage is 144*32+100=4708 original checks.
   Compare resolved reference versus independently rebuilt row feasibility and
   candidate sums, while distinguishing inconclusive reference optimization
   from known feasible/empty-domain evidence. A single successful comparison
   cannot fulfill this coverage contract. Shared code/version repetition alone
   is deterministic reproducibility; acceptance also needs own raw checks and
   enforced independent artifact review.

## Planted corruption cases for later verification

These are future isolated checker fixtures derived from existing planned rows
and metadata. They add no scientific scenarios, seeds, target values or results.
Never modify canonical raw files, manifests or archived evidence. Test checksum
rejection on disposable copies; test semantic checks on in-memory copies fed
to pure checker functions so a hash rejection does not mask a semantic defect.
Retain expected versus actual detection receipts during authorized P6 testing.

| Isolated mutation | Required detection/outcome |
| --- | --- |
| Raw byte change under unchanged checksum | Native integrity rejection |
| Missing/extra/duplicate planned scenario or seed; empty inventory | Exact inventory rejection, no vacuous pass |
| Duplicate/reordered/missing row, mismatched metrics.csv line | Row coverage/alignment rejection |
| MC P/qw/qs or deterministic case_id changed; gains reversed | Manifest/case/domain mismatch |
| One seeded gain or cross-setting row changed | Seed reproduction/common-draw mismatch |
| NaN feasible a_star/sum, illegal split, unknown status or boolean token | Explicit finite/domain/schema rejection before max/CI |
| rw increased and rs reduced by same amount; individual OMA rates swapped while total retained | Per-field independent recomputation mismatch despite preserved total |
| Paired difference changed with all sums intact | Independent difference and rebuilt CI mismatch |
| All stored OMA indicators and categories changed consistently | Independent OMA/classification mismatch despite internal ledger consistency |
| sum/a_star replaced by zero outside its feasible mask | Undefined-output rejection; zero is not undefined |
| Exact singleton witness text changed or a rational boundary labeled feasible without direct satisfaction | Exact original-SINR certificate rejection or qualified unresolved result |
| Fixed/grid sum increased, grid_a off-grid, grid miss labeled infeasible, loss summary replaced by zero | Own allocation/max/mask/loss checks detect the mutation |
| Oracle row/input reassigned or omitted, tighter record missing/wrong settings/failed status hidden | Reference coverage/binding/status diagnostics reject incomplete comparison |
| Wrong statistical denominator, variance divisor, 100-event qualification or zero-event certainty flag | Independently rebuilt conditional/event policy mismatch |
| OMA-reference point/ordering/trend flag changed | Source-equation and unfiltered-mean comparison mismatch |
| Coherent fixture with no paired observations | Undefined paired mean/CI; no fabricated zero or precision success |

## Required future evidence and completion criteria

Produce analysis-only receipts containing: actual input/source/manifest hashes;
fresh job inventory and row coverage; full field/mask errors; independent status
and ambiguity counts; rebuilt ledgers and summaries; own fixed/grid comparisons;
conditional/event/reference statistics; separately labeled oracle/tighter replay;
actual runtime/memory/failure logs; and planted-corruption detection receipts.
Each weak native check must point to its supplement rather than inheriting a
blanket PASS. Index every finding E01-E11 to the corresponding supplemental
evidence and retain any unresolved coverage item.

Map evidence to all eight native dimensions (independent-recomputation, units,
constraints, convergence, fairness, statistical-precision, sensitivity,
ablations) and the existing P1-P7 predictions. Do not infer universal exact
proofs from finite checks. Classify hard mismatches as failures, uncertainty or
unmet event/precision/budget qualifications as inconclusive, and exact or finite
agreement according to its actual evidence. Preserve failed receipts and logs.

A future complete P6 handoff requires the canonical fresh gate prerequisites,
actual native execution receipts, all declared supplemental coverage or explicit
remaining limitations, and a fresh enforced independent review. No such
execution, verdict or acceptance is performed or claimed by this document.
