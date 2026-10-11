"""Broadcast closed-form optimizer for the G4-approved scalar model.

Status is feasible/infeasible/unresolved. NaN is an undefined numeric output,
including the feasibility indicator of an unresolved instance. The boundary
band is a trigger for a certificate, never a relaxed QoS constraint.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

LN2 = np.log(2.0)


def _inputs(P, gw, gs, qw, qs):
    arrays = np.broadcast_arrays(*[np.asarray(x, dtype=float) for x in (P, gw, gs, qw, qs)])
    if any(np.any(~np.isfinite(x)) or np.any(x < 0) for x in arrays):
        raise ValueError("Inputs must be finite and nonnegative")
    if np.any(arrays[1] > arrays[2]):
        raise ValueError("Channel gains must be ordered gw <= gs")
    return arrays


def direct_rates(P, gw, gs, a):
    """Evaluate original three SINRs; accepts broadcast arrays, no QoS logic."""
    P, gw, gs, a = np.broadcast_arrays(*[np.asarray(x, dtype=float) for x in (P, gw, gs, a)])
    if any(np.any(~np.isfinite(x)) or np.any(x < 0) for x in (P, gw, gs)):
        raise ValueError("Power and gains must be finite and nonnegative")
    if np.any(gw > gs) or np.any((a < 0) | (a > 1) | ~np.isfinite(a)):
        raise ValueError("Ordered gains and finite split in [0,1] required")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore", under="ignore"):
        A, B = P * gw, P * gs
        ww = ((1.0 - a) * A) / (1.0 + a * A)
        ws = ((1.0 - a) * B) / (1.0 + a * B)
        ss = a * B
        rw_site, cw_at_s, rs = np.log1p(ww) / LN2, np.log1p(ws) / LN2, np.log1p(ss) / LN2
    return {
        "gamma_ww": ww,
        "gamma_ws": ws,
        "gamma_ss": ss,
        "rw_site": rw_site,
        "cw_at_s": cw_at_s,
        "rw": np.minimum(rw_site, cw_at_s),
        "rs": rs,
        "sum_rate": np.minimum(rw_site, cw_at_s) + rs,
    }


def _rational_interval(P, gw, gs, qw, qs):
    """Exact analytic certificate for integer targets and exact float inputs."""
    if not (qw.is_integer() and qs.is_integer() and max(qw, qs) <= 1024):
        return None
    A = Fraction(P) * Fraction(gw)
    B = Fraction(P) * Fraction(gs)
    tw, ts = Fraction(2 ** int(qw) - 1), Fraction(2 ** int(qs) - 1)
    if B == 0:
        return (qw == qs == 0, Fraction(0), Fraction(1))
    lo = ts / B
    if A == 0:
        return (qw == 0 and lo <= 1, lo, Fraction(1))
    hi = min(Fraction(1), (A - tw) / (A * (1 + tw)))
    return (lo <= hi, lo, hi)


def _rational_oma(P, gw, gs, qw, qs):
    if not (qw.is_integer() and qs.is_integer() and max(qw, qs) <= 1024):
        return None
    return (
        Fraction(P) * Fraction(gw) >= 2 ** (2 * int(qw)) - 1
        and Fraction(P) * Fraction(gs) >= 2 ** (2 * int(qs)) - 1
    )


def solve(P, gw, gs, qw, qs, *, rate_tolerance=1e-9, split_tolerance=1e-12):
    """Return array-valued ledger and numerical optimizer, with conservative boundaries.

    Input scalars yield zero-dimensional arrays. Integer-QoS certificates use
    exact rational representations of the supplied binary64 P/gains, not their
    rounded products. Normal separated classifications are numerical evaluations,
    not machine-certified bounds on all real arithmetic.
    """
    if not np.isfinite(rate_tolerance) or rate_tolerance <= 0:
        raise ValueError("Positive finite rate_tolerance required")
    if not np.isfinite(split_tolerance) or split_tolerance <= 0:
        raise ValueError("Positive finite split_tolerance required")
    original = _inputs(P, gw, gs, qw, qs)
    shape = original[0].shape
    P, gw, gs, qw, qs = [x.ravel() for x in original]
    n = P.size
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        A, B = P * gw, P * gs
        ts = np.expm1(qs * LN2)
        lo = np.divide(ts, B, out=np.zeros(n), where=B > 0)
        # (A-Tw)/(A*(1+Tw)) in a form avoiding Tw and the large denominator.
        hi = np.exp(-qw * LN2) + np.divide(np.expm1(-qw * LN2), A, out=np.zeros(n), where=A > 0)
        hi = np.minimum(1.0, hi)
    zero = B == 0
    hi = np.where((A == 0) | zero, 1.0, hi)
    status = np.full(n, "unresolved", dtype="U10")
    certificate = np.full(n, "none", dtype="U32")
    exact_split = np.full(n, "", dtype=object)
    interval_singleton = np.zeros(n, dtype=bool)
    numeric_domain = (
        np.isfinite(A)
        & np.isfinite(B)
        & ~((P > 0) & (gw > 0) & (A == 0))
        & ~((P > 0) & (gs > 0) & (B == 0))
        & ~((qs > 0) & (ts == 0))
        & ~((qw > 0) & (np.expm1(-qw * LN2) == 0))
    )
    zero_ok = numeric_domain & zero
    status[zero_ok] = np.where((qw[zero_ok] == 0) & (qs[zero_ok] == 0), "feasible", "infeasible")
    certificate[zero_ok] = "exact-zero"
    weak_impossible = numeric_domain & (A == 0) & (qw > 0)
    status[weak_impossible] = "infeasible"
    certificate[weak_impossible] = "exact-zero-weak"
    ordinary = numeric_domain & ~zero & ~weak_impossible
    boundary = ordinary & (np.abs(lo - hi) <= split_tolerance)
    status[ordinary & ~boundary & (lo <= hi)] = "feasible"
    status[ordinary & ~boundary & (lo > hi)] = "infeasible"
    certificate[ordinary & ~boundary] = "binary64-separated"
    # Overflowing targets cannot be met by a finite binary64 SNR. This statement
    # is supported by capacity separation, not a clamped target exponent.
    capacity_s = np.log1p(B) / LN2
    obvious_large = ordinary & (qs > capacity_s + rate_tolerance)
    status[obvious_large] = "infeasible"
    certificate[obvious_large] = "binary64-capacity-separated"
    for j in np.flatnonzero(boundary):
        cert = _rational_interval(*[float(x[j]) for x in (P, gw, gs, qw, qs)])
        if cert is not None:
            ok, lower, upper = cert
            status[j] = "feasible" if ok else "infeasible"
            certificate[j] = "exact-rational"
            lo[j], hi[j] = float(lower), float(upper)
            interval_singleton[j] = ok and lower == upper
            if ok:
                exact_split[j] = str(upper)
    candidate = np.where(status == "feasible", hi, np.nan)
    # Undefined rows are evaluated at zero only to avoid leaking NaNs through
    # input validation; their returned rate/SINR outputs remain undefined.
    safe_a = np.where(np.isfinite(candidate), candidate, 0.0)
    safe_power = np.where(numeric_domain, P, 0.0)
    rates = direct_rates(safe_power, gw, gs, safe_a)
    residual_w = rates["rw"] - qw
    residual_s = rates["rs"] - qs
    sic_residual = rates["cw_at_s"] - rates["rw_site"]
    candidate_violation = (status == "feasible") & (
        (residual_w < -rate_tolerance)
        | (residual_s < -rate_tolerance)
        | (sic_residual < -rate_tolerance)
        | ~np.isfinite(rates["sum_rate"])
    )
    # Retain failed candidate diagnostics but withhold a purported optimum.
    status[candidate_violation] = "unresolved"
    candidate_ok = status == "feasible"
    feasible = np.where(candidate_ok, 1.0, np.where(status == "infeasible", 0.0, np.nan))
    oma_rw, oma_rs = np.log1p(A) / (2 * LN2), np.log1p(B) / (2 * LN2)
    ow, os = oma_rw - qw, oma_rs - qs
    oma_boundary = numeric_domain & (
        ((qw > 0) & (np.abs(ow) <= rate_tolerance)) | ((qs > 0) & (np.abs(os) <= rate_tolerance))
    )
    oma_status = np.full(n, "unresolved", dtype="U10")
    oma_certificate = np.full(n, "none", dtype="U32")
    oma_bad = numeric_domain & ((ow < -rate_tolerance) | (os < -rate_tolerance))
    oma_good = numeric_domain & ~oma_boundary & ~oma_bad
    oma_status[oma_bad] = "infeasible"
    oma_status[oma_good] = "feasible"
    oma_certificate[oma_bad | oma_good] = "binary64-separated"
    # An exact-zero positive target is infeasible even when below the rate band.
    oma_zero_bad = numeric_domain & (((A == 0) & (qw > 0)) | ((B == 0) & (qs > 0)))
    oma_status[oma_zero_bad] = "infeasible"
    oma_certificate[oma_zero_bad] = "exact-zero"
    for j in np.flatnonzero(oma_boundary & ~oma_bad & ~oma_zero_bad):
        ok = _rational_oma(*[float(x[j]) for x in (P, gw, gs, qw, qs)])
        if ok is not None:
            oma_status[j] = "feasible" if ok else "infeasible"
            oma_certificate[j] = "exact-rational"
    oma_feasible = np.where(
        oma_status == "feasible", 1.0, np.where(oma_status == "infeasible", 0.0, np.nan)
    )
    resolved = np.isfinite(feasible) & np.isfinite(oma_feasible)
    category = np.full(n, "unresolved", dtype="U10")
    for u, v in ((0, 0), (0, 1), (1, 0), (1, 1)):
        category[resolved & (feasible == u) & (oma_feasible == v)] = f"n{u}{v}"
    result = {
        "status": status,
        "feasible": feasible,
        "certificate": certificate,
        "A": A,
        "B": B,
        "interval_lower": lo,
        "interval_upper": hi,
        "a_star": np.where(candidate_ok, candidate, np.nan),
        "candidate_a": candidate,
        "exact_split": exact_split,
        "boundary_flag": boundary,
        "numeric_domain": numeric_domain,
        "candidate_violation": candidate_violation,
        "singleton": interval_singleton,
        "optimizer_unique": candidate_ok & (((P > 0) & (gs > gw)) | interval_singleton),
        "nonunique": candidate_ok & ~(((P > 0) & (gs > gw)) | interval_singleton),
        "candidate_constraints_pass": np.isfinite(candidate)
        & (residual_w >= 0)
        & (residual_s >= 0)
        & (sic_residual >= 0),
        "candidate_within_rate_tolerance": np.isfinite(candidate)
        & (residual_w >= -rate_tolerance)
        & (residual_s >= -rate_tolerance)
        & (sic_residual >= -rate_tolerance),
        "oma_status": oma_status,
        "oma_feasible": oma_feasible,
        "oma_certificate": oma_certificate,
        "oma_boundary_flag": oma_boundary,
        "oma_rw": oma_rw,
        "oma_rs": oma_rs,
        "oma_sum": oma_rw + oma_rs,
        "oma_residual_w": ow,
        "oma_residual_s": os,
        "category": category,
        "residual_w": np.where(np.isfinite(candidate), residual_w, np.nan),
        "residual_s": np.where(np.isfinite(candidate), residual_s, np.nan),
        "sic_residual": np.where(np.isfinite(candidate), sic_residual, np.nan),
        "paired_difference": np.where(
            (category == "n11"), rates["sum_rate"] - oma_rw - oma_rs, np.nan
        ),
    }
    for name, value in rates.items():
        result[name] = np.where(candidate_ok, value, np.nan)
        result["candidate_" + name] = np.where(np.isfinite(candidate), value, np.nan)
    return {name: value.reshape(shape) for name, value in result.items()}
