# Author certificate for the fractional boundary

Status: author deduction; independent numerical-results review remains pending.
The active verifier and all saved unresolved labels remain unchanged.

## Exact approved case

The deterministic case has P = 1, g_w = g_s = 1 and q_w = q_s = 1/2.
It appears at rows 16, 36, 56, 76 and 96 of the manifest bound in the JSON receipt.

## NOMA derivation

Both weak-message decoding sites have the same capacity. The approved model
reduces to R_w(a) = log2(2/(1+a)) and R_s(a) = log2(1+a).
The weak target requires 1+a <= sqrt(2), and the strong target requires
1+a >= sqrt(2). Thus the exact real feasible set is the singleton
a = sqrt(2)-1. Both weak decoding sites and the strong rate are exactly 1/2;
the total is 1 bit/s/Hz. This is a single approved-case deduction.

The polynomial f(a) = (1+a)^2-2 is strictly increasing on [0,1]. Exact Fraction
arithmetic confirms f(recorded lower bracket) < 0 < f(recorded upper bracket)
for each of the five actual saved rows. The root lies inside those brackets.

Every finite binary64 number is rational, while sqrt(2)-1 is irrational. Hence
no binary64 split satisfies both exact real inequalities simultaneously. The
saved rows contain no accepted optimizer or exact-split certificate. A rounded
split and a real-model algebraic witness have different representational roles.

## OMA derivation

Each matched full-power slot has capacity log2(2)=1. The whole-block factor
1/2 gives each user's rate exactly 1/2, with total 1 bit/s/Hz. Both exact real
targets are met at equality. The recorded OMA rates agree numerically, while
the current conservative boundary classifier leaves their labels unresolved.

## Consequence for the current run

This explains the known fractional-boundary uncertainty. It does not amend
the frozen verifier, upgrade stored statuses, replace the pending independent
results review or approve a scientific gate. The full corrected run and its
combined assessment must retain their actual uncertainty. A proposed algebraic
certificate implementation belongs in a separately reviewed change, with any
required PI decisions before changes to locked source or protocol.
