"""Independent original-SINR constraint search over the full split domain.

No analytic-module imports, closed-form QoS endpoints, or derivative-sign
optimizer. Rational feasibility certificates and numerical objective checks
are explicitly different evidence. Numerical secant bounds are not rigorous
interval arithmetic certificates.
"""

from __future__ import annotations

import math
from fractions import Fraction

from scipy.optimize import minimize_scalar


def direct_rates(P, gw, gs, a):
    """Original decoding-site SINRs, independently implemented scalar path."""
    if not all(math.isfinite(x) and x >= 0 for x in (P, gw, gs)):
        raise ValueError("Power and gains must be finite nonnegative scalars")
    if gw > gs or not math.isfinite(a) or not 0 <= a <= 1:
        raise ValueError("Ordered gains and split in [0,1] required")
    received_w, received_s = P * gw, P * gs
    weak_at_w = (1 - a) * received_w / (1 + a * received_w)
    weak_at_s = (1 - a) * received_s / (1 + a * received_s)
    strong_after_sic = a * received_s
    capacity_w = math.log1p(weak_at_w) / math.log(2)
    capacity_sic = math.log1p(weak_at_s) / math.log(2)
    strong = math.log1p(strong_after_sic) / math.log(2)
    return {
        "gamma_ww": weak_at_w,
        "gamma_ws": weak_at_s,
        "gamma_ss": strong_after_sic,
        "rw_site": capacity_w,
        "cw_at_s": capacity_sic,
        "rw": min(capacity_w, capacity_sic),
        "rs": strong,
        "sum_rate": min(capacity_w, capacity_sic) + strong,
    }


def _exact_constraints(P, gw, gs, qw, qs):
    # The only target conversion here is the exact integer 2**q-1. Constraints
    # are evaluated as original SINRs; there is no endpoint formula.
    if not (qw.is_integer() and qs.is_integer() and max(qw, qs) <= 1024):
        return None
    power, weak, strong = map(Fraction, (P, gw, gs))
    received_w, received_s = power * weak, power * strong
    target_w, target_s = 2 ** int(qw) - 1, 2 ** int(qs) - 1

    def residuals(a):
        at_w = (1 - a) * received_w / (1 + a * received_w) - target_w
        at_s = (1 - a) * received_s / (1 + a * received_s) - target_w
        post_sic = a * received_s - target_s
        return min(at_w, at_s), post_sic

    return residuals


def _bracket(predicate, increasing, zero, one, tolerance, cap):
    """Bracket a monotone constraint threshold from original-domain endpoints.

    Returned inner and outer bounds retain the true threshold for exact
    predicates. Float predicates provide numerical bracketing only.
    """
    at_zero, at_one = predicate(zero), predicate(one)
    if increasing:
        if at_zero:
            return zero, zero, 0, True
        if not at_one:
            return None, None, 0, True
    else:
        if at_one:
            return one, one, 0, True
        if not at_zero:
            return None, None, 0, True
    left, right = zero, one
    for count in range(1, cap + 1):
        midpoint = (left + right) / 2
        if midpoint == left or midpoint == right:
            return left, right, count, True
        satisfied = predicate(midpoint)
        if satisfied == increasing:
            right = midpoint
        else:
            left = midpoint
        if float(right - left) <= tolerance:
            return left, right, count, True
    return left, right, cap, False


def _rational_witness(residuals, brackets):
    """Try rational reconstruction, then check original SINRs exactly.

    Reconstruction is a search heuristic. The exact direct check supplies the
    certificate. Simultaneously active weak/strong constraints certify a
    singleton by their monotone QoS sets, without endpoint algebra.
    """
    candidates = {Fraction(0), Fraction(1)}
    for x in brackets:
        for denominator in (1024, 65536, 1000000, 2**32):
            candidates.add(x.limit_denominator(denominator))
    for candidate in sorted(candidates):
        if 0 <= candidate <= 1:
            w, s = residuals(candidate)
            if w >= 0 and s >= 0:
                return candidate, w == 0 and s == 0
    return None, False


def _concavity_upper_bound(objective, low, high, best_x, best_f, split_tolerance):
    """Numerical supporting-line envelope from direct objective secants.

    For exact concave f, the left secant at t upper bounds slopes to its
    right and the right secant lower bounds slopes to its left. Floating
    evaluation and finite secants receive a roundoff allowance, not a formal
    validated-numerics error proof.
    """
    width = high - low
    if width <= 0:
        return best_f, 0.0
    h = min(width / 4, max(4 * split_tolerance, width * 1e-5))
    center = min(max(best_x, low + h), high - h)
    left, right = center - h, center + h
    if not low <= left < center < right <= high:
        return math.nan, math.nan
    fl, ft, fr = objective(left), objective(center), objective(right)
    slope_left, slope_right = (ft - fl) / (center - left), (fr - ft) / (right - center)
    upper_left = ft + max(0.0, slope_right * (low - center))
    upper_right = ft + max(0.0, slope_left * (high - center))
    roundoff_allowance = 256 * math.ulp(max(1.0, abs(fl), abs(ft), abs(fr), abs(best_f)))
    upper = max(best_f, upper_left, upper_right) + roundoff_allowance
    return upper, max(0.0, upper - best_f)


def solve(
    P,
    gw,
    gs,
    qw,
    qs,
    *,
    rate_tolerance=1e-9,
    split_tolerance=1e-12,
    objective_tolerance=1e-7,
    max_root_iterations=96,
    max_optimizer_iterations=256,
):
    """Scalar oracle; caps/failures and ambiguous feasibility stay explicit.

    ``feasibility_certificate`` is exact-rational only for exact Fraction
    comparisons. Objective optimality is always numerical (except a proved
    singleton/constant zero domain); a SciPy success flag alone is insufficient.
    """
    P, gw, gs, qw, qs = map(float, (P, gw, gs, qw, qs))
    if not all(math.isfinite(x) and x >= 0 for x in (P, gw, gs, qw, qs)) or gw > gs:
        raise ValueError("Finite nonnegative original inputs and ordered gains required")
    if not all(
        math.isfinite(x) and x > 0 for x in (rate_tolerance, split_tolerance, objective_tolerance)
    ):
        raise ValueError("Positive finite tolerances required")
    if (
        type(max_root_iterations) is not int
        or max_root_iterations < 1
        or type(max_optimizer_iterations) is not int
        or max_optimizer_iterations < 1
    ):
        raise ValueError("Positive integer iteration caps required")
    result = {
        "status": "unresolved",
        "feasible": math.nan,
        "feasibility_certificate": "none",
        "optimality_status": "not-established",
        "a_star": math.nan,
        "candidate_a": math.nan,
        "exact_split": "",
        "rw": math.nan,
        "rs": math.nan,
        "sum_rate": math.nan,
        "residual_w": math.nan,
        "residual_s": math.nan,
        "sic_residual": math.nan,
        "objective_upper_bound": math.nan,
        "objective_gap_bound": math.nan,
        "root_iterations": 0,
        "optimizer_iterations": 0,
        "optimizer_evaluations": 0,
        "singleton": False,
        "inner_lower": math.nan,
        "inner_upper": math.nan,
        "outer_lower": math.nan,
        "outer_upper": math.nan,
        "reason": "",
        "rate_tolerance": rate_tolerance,
        "split_tolerance": split_tolerance,
        "objective_tolerance": objective_tolerance,
        "max_root_iterations": max_root_iterations,
        "max_optimizer_iterations": max_optimizer_iterations,
    }
    rw_oma = math.log1p(P * gw) / (2 * math.log(2))
    rs_oma = math.log1p(P * gs) / (2 * math.log(2))
    result.update(oma_rw=rw_oma, oma_rs=rs_oma, oma_sum=rw_oma + rs_oma)
    numeric_domain = (
        math.isfinite(P * gs)
        and not (P > 0 and gs > 0 and P * gs == 0)
        and not (P > 0 and gw > 0 and P * gw == 0)
    )
    if not numeric_domain:
        result["reason"] = "Received product overflow/underflow outside binary64 execution domain"
        return result
    exact = _exact_constraints(P, gw, gs, qw, qs)
    if exact is not None:
        residuals = exact
        zero, one = Fraction(0), Fraction(1)
        result["feasibility_certificate"] = "exact-rational"
    else:

        def residuals(a):
            rates = direct_rates(P, gw, gs, a)
            return rates["rw"] - qw, rates["rs"] - qs

        zero, one = 0.0, 1.0
        result["feasibility_certificate"] = "numerical-direct-bracket"
    weak = _bracket(
        lambda a: residuals(a)[0] >= 0, False, zero, one, split_tolerance, max_root_iterations
    )
    strong = _bracket(
        lambda a: residuals(a)[1] >= 0, True, zero, one, split_tolerance, max_root_iterations
    )
    result["root_iterations"] = weak[2] + strong[2]
    if not weak[3] or not strong[3]:
        result["reason"] = "Root bracket iteration cap reached"
        return result
    if weak[0] is None or strong[0] is None:
        # Float endpoint failures within the rate band cannot prove infeasibility.
        endpoints = [direct_rates(P, gw, gs, a) for a in (0.0, 1.0)]
        separated = (
            qw > endpoints[0]["rw"] + rate_tolerance or qs > endpoints[1]["rs"] + rate_tolerance
        )
        exact_zero = (P * gw == 0 and qw > 0) or (P * gs == 0 and qs > 0)
        if exact is not None or separated or exact_zero:
            result.update(
                status="infeasible",
                feasible=0.0,
                reason="Original endpoint capacity cannot satisfy a QoS constraint",
            )
        else:
            result["reason"] = "Endpoint feasibility inside numerical rate band"
        return result
    weak_inner, weak_outer = weak[0], weak[1]
    strong_outer, strong_inner = strong[0], strong[1]
    result.update(
        inner_lower=float(strong_inner),
        inner_upper=float(weak_inner),
        outer_lower=float(strong_outer),
        outer_upper=float(weak_outer),
    )
    if strong_outer > weak_outer:
        if exact is not None or float(strong_outer - weak_outer) > 2 * split_tolerance:
            result.update(
                status="infeasible",
                feasible=0.0,
                reason="Disjoint original-constraint outer brackets",
            )
        else:
            result["reason"] = "Overlapping numerical uncertainty band"
        return result
    witness, singleton = (None, False)
    if exact is not None:
        witness, singleton = _rational_witness(
            residuals, [strong_outer, strong_inner, weak_inner, weak_outer]
        )
    # The all-zero domain has both constraints active at every point, so two
    # active constraints do not mean a singleton there.
    singleton = singleton and P * gw > 0 and P * gs > 0
    if witness is not None:
        exact_w, exact_s = residuals(witness)
        singleton = singleton or (witness == 1 and P * gs > 0 and exact_s == 0)
        singleton = singleton or (witness == 0 and P * gw > 0 and exact_w == 0)
    result["singleton"] = singleton
    if singleton:
        low = high = float(witness)
        result["exact_split"] = str(witness)
    elif strong_inner <= weak_inner and (
        exact is not None or float(weak_inner - strong_inner) > 2 * split_tolerance
    ):
        low, high = float(strong_inner), float(weak_inner)
        # Move floating representations inward; exact witnesses remain stored.
        if exact is not None and low < high:
            if strong_inner > 0:
                low = math.nextafter(low, math.inf)
            if weak_inner < 1:
                high = math.nextafter(high, -math.inf)
    elif witness is not None:
        result["exact_split"] = str(witness)
        result["reason"] = "Exact feasible witness found, maximum unresolved in narrow interval"
        return result
    else:
        result["reason"] = "Narrow/singleton domain without an exact direct certificate"
        return result
    if low > high:
        result["reason"] = "Certified inner interval not representable in binary64"
        return result

    def objective(a):
        return direct_rates(P, gw, gs, a)["sum_rate"]

    candidates = [low, high]
    solver_ok = True
    if low < high:
        answer = minimize_scalar(
            lambda a: -objective(a),
            bounds=(low, high),
            method="bounded",
            options={"xatol": split_tolerance, "maxiter": max_optimizer_iterations},
        )
        result["optimizer_iterations"] = int(answer.nit)
        result["optimizer_evaluations"] = int(answer.nfev)
        solver_ok = bool(answer.success)
        if math.isfinite(answer.x) and low <= answer.x <= high:
            candidates.append(float(answer.x))
    best = max(candidates, key=objective)
    evaluated = direct_rates(P, gw, gs, best)
    result.update(candidate_a=best, **{"candidate_" + k: v for k, v in evaluated.items()})
    result.update(
        residual_w=evaluated["rw"] - qw,
        residual_s=evaluated["rs"] - qs,
        sic_residual=evaluated["cw_at_s"] - evaluated["rw_site"],
    )
    bound_low = low if singleton else float(strong_outer)
    bound_high = high if singleton else float(weak_outer)
    upper, gap = _concavity_upper_bound(
        objective, bound_low, bound_high, best, evaluated["sum_rate"], split_tolerance
    )
    result.update(objective_upper_bound=upper, objective_gap_bound=gap)
    if not solver_ok:
        result["reason"] = "Bounded scalar optimizer did not converge"
        return result
    if min(result["residual_w"], result["residual_s"], result["sic_residual"]) < -rate_tolerance:
        result["reason"] = "Direct numerical candidate violated a constraint"
        return result
    if not math.isfinite(gap) or gap > objective_tolerance:
        result["reason"] = "Numerical concavity objective gap exceeds tolerance"
        return result
    result.update(
        status="feasible",
        feasible=1.0,
        a_star=best,
        **evaluated,
        optimality_status="exact-singleton" if singleton else "numerical-concavity-bound",
        reason="Original constraints and bounded scalar objective check accepted",
    )
    return result
