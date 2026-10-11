# Exact optimizer and independent validation proposal

Status: P4 specification for idea-01; no implementation or simulation run.
Inputs are finite P >= 0, ordered 0 <= g_w <= g_s, fixed q_w,q_s >= 0.
All arithmetic and comparisons below are exact real arithmetic. Return a
separate feasibility status, split, individual rates, decoding-site rates
and sum; undefined values stay undefined for an infeasible scheme.

## Analytic optimizer

```text
Reject inputs outside the specified domain.
NOMA_feasible <- false; infeasibility_declared <- false
A <- P*g_w; B <- P*g_s
T_w <- 2^q_w - 1; T_s <- 2^q_s - 1
If B = 0:
    If q_w > 0 or q_s > 0:
        NOMA <- infeasible; infeasibility_declared <- true
    Else:
        NOMA_feasible <- true
        interval <- [0,1]; a_star <- 1; all rates <- 0
Else:
    L <- T_s/B
    If A = 0:
        If q_w > 0:
            NOMA <- infeasible; infeasibility_declared <- true
        Else: U <- 1
    Else: U <- min(1,(A-T_w)/(A*(1+T_w)))
    If not infeasibility_declared:
        If L > U: NOMA <- infeasible
        Else:
            NOMA_feasible <- true
            interval <- [L,U]; a_star <- U
            R_w <- log2((1+A)/(1+a_star*A))
            R_s <- log2(1+a_star*B)
            C_w_at_s <- log2((1+B)/(1+a_star*B))
            F_star <- R_w+R_s
            optimizer_unique <- (B>A) or (L=U)
            check direct QoS and both weak decoding sites
R_w_OMA <- (1/2)*log2(1+A); R_s_OMA <- (1/2)*log2(1+B)
OMA_feasible <- R_w_OMA >= q_w and R_s_OMA >= q_s
Record both feasibility indicators and category.
If NOMA_feasible and OMA_feasible: record paired sum difference
Else: paired sum difference <- undefined
```

The sum-rate optimum is unique at equal gains only when the feasible
interval is a singleton. The deterministic choice U for all ties is a
representation convention, not an additional physical assumption.
Do not clamp an empty interval or declare a failed instance a zero optimum.
The mathematical optimizer takes O(1) operations/storage per block.

## Structurally independent scalar oracle proposal

A separately written validator should receive the original inputs, not
the analytic interval or endpoint. It should evaluate the original SINRs
at both weak-message decoding sites and the post-SIC strong rate directly,
using `min(weak capacity, weak capacity at strong receiver)`.

```text
Read original P,g_w,g_s,q_w,q_s and independently check their domain.
Compute rates from original SINRs for candidate a in full [0,1].
Check a,1-a >= 0 and both QoS constraints plus strong SIC decodability.
Search full [0,1] using a bounded scalar feasibility/optimization procedure
    with independent constraint handling and a P5-approved certificate.
Retain infeasible, feasible, unresolved-numerical statuses distinctly.
For a singleton/boundary case, resolve feasibility independently through
    direct monotone constraint root bracketing or higher precision.
Compare certified maximum and direct candidate feasibility with analytic output.
Check independently evaluated matched OMA and complete category counts.
```

The oracle must not call the optimizer, reuse its L/U formulas, simply
evaluate U, or assume a copied derivative sign. A finite grid alone is
insufficient: it may miss a narrow interval or singleton and cannot certify
exact infeasibility. If P5 chooses a grid, it needs independently derived
error/coverage handling and unresolved statuses; if it chooses a solver,
its convergence conditions and certificates must be specified. Separate
monotone root bracketing on the original rate constraints can resolve
boundaries without copying the closed-form bounds, but the stopping rule,
precision and caps remain P5 choices. No specific oracle is accepted here.

No scalar oracle complexity or convergence guarantee is fixed without a
chosen procedure. For K candidate evaluations its evaluation cost is O(K)
with O(1) streaming storage, excluding certificate and precision costs;
K is an unspecified work count, not a chosen resolution. Later multi-block
aggregation is O(N) work and may use O(1) streaming summary storage, with
per-block evidence storage specified at P5.

## Numerical risks and falsification cases for P5

Cover P=0; g_w=0; g_s=0; equal gains; both targets zero; each single zero
target; infeasible targets; a=0/1; singleton and nearly singleton intervals.
Ensure overflow, cancellation and representability do not silently alter
feasibility. Prospective stable forms include log1p for rates and expm1
for targets; no package, precision, tolerance, stopping rule, distribution,
QoS/SNR grid, seed, count or solver cap is selected. Numerical tolerances:
not stated; P5 approval required.

Any directly infeasible analytic candidate, independently certified better
feasible split, genuine OMA-only exact instance, or negative paired sum
difference contradicts a scoped claim and must be retained and diagnosed.
Do not erase small differences using an unapproved tolerance. This is a
validation proposal, not a claim that checks were run or passed.
