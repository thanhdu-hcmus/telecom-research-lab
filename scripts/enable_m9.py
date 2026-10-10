from build_support import evaluation, role, skill

skill(
    "results-verification",
    "Use by results_verifier in approved P6 to independently recompute metrics, test predictions and build numeric claim lineage.",
    """
Read artifacts and raw manifest outputs only, not author reasoning. Write only
analysis/. Recompute metrics with an independent implementation; never call the
simulator's metric function. Check units/path loss/noise, constraints/convergence,
common draws/equal power/CSI/QoS, baseline ordering, sensitivities and ablations.
Test approved predictions with declared regimes/tolerances. Averages need target
CI halfwidth; outage needs >=100 observed events and exact/Wilson CIs. Zero events
means an upper bound. Save independent checks, input hashes and verification items.
Triage failures as implementation-bug, theory-error, approximation-gap or
statistical-noise. Inconclusive is not PASS. Every numeric claim must name a valid
manifest output and executable JSON computation, with intended manuscript usage.
Use lab verify and lab.verification.evaluate_claim; never invent a claim value.
""",
)
role(
    "results_verifier",
    "Independently recompute from raw draws and manifest outputs, enforce CI/event counts and fair budgets, validate claim computations; write only analysis/ and never approve gates.",
)
bugs = """# CC0 planted result diagnostics\n[B1] Parameter SNR=10 dB. Code rho=10**(snr_db/10), then rho=10**(rho/10) before use; for snr_db=20 second conversion gives 10^10 instead of100.\n[B2] Outage plot reports 0.001 from 1 event in1000 trials as precise with no CI.\n[B3] Model power path gain=d^-3; code sets amplitude=d^-3 and squares it, effectively power d^-6.\n[B4] Proposed method uses1W, baseline0.1W; claim improvement at same power.\n"""
clean = """# CC0 clean control\nSNR=20dB converted once to100 linear. Path amplitude=d^(-3/2), gain=d^-3.\nProposed and baseline1W, equal bandwidth/CSI/QoS and same recorded channels.\n200000 trials,200 outage events, exact95% binomial interval reported.\nRates and units independently recomputed; no universal claim beyond scenario.\n"""
evaluation(
    "verifier-planted-bugs",
    "results_verifier",
    "Read fixture bugs.md and clean.md and results-verification. Return JSON {bugs:[{id,location,issue,triage,fix}],clean_findings:[]}. Distinguish implementation errors from insufficient statistical evidence; four bracketed issue labels identify locations. Do not alter results.",
    {"bugs.md": bugs, "clean.md": clean},
    {
        "triage": {
            "B1": "implementation-bug",
            "B2": "statistical-noise",
            "B3": "implementation-bug",
            "B4": "implementation-bug",
        }
    },
)
