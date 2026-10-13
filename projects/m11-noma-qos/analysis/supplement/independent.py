"""Independent original-constraint calculations. No production metric imports."""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
from scipy.special import exp1
from scipy.stats import beta, t

RATE = 1e-9
SPLIT = 1e-12
OBJECTIVE = 1e-7
ROOT_CAP = 96
FIELDS = "gamma_ww gamma_ws gamma_ss rw_site cw_at_s rw rs sum_rate".split()
CHANNEL_COLUMNS = "row P gw gs qw qs case_id status feasible certificate A B interval_lower interval_upper a_star candidate_a exact_split boundary_flag numeric_domain candidate_violation singleton optimizer_unique nonunique candidate_constraints_pass candidate_within_rate_tolerance oma_status oma_feasible oma_certificate oma_boundary_flag oma_rw oma_rs oma_sum oma_residual_w oma_residual_s category residual_w residual_s sic_residual paired_difference gamma_ww candidate_gamma_ww gamma_ws candidate_gamma_ws gamma_ss candidate_gamma_ss rw_site candidate_rw_site cw_at_s candidate_cw_at_s rw candidate_rw rs candidate_rs sum_rate candidate_sum_rate fixed_feasible fixed_sum grid_found_feasible grid_sum grid_a".split()
METRIC_COLUMNS = "feasible oma_feasible sum_rate oma_sum paired_difference fixed_feasible fixed_sum grid_found_feasible grid_sum grid_a".split()


def number(x):
    return float(x)


def boolean(x):
    if x is True or x == "True":
        return True
    if x is False or x == "False":
        return False
    raise ValueError(f"Invalid boolean: {x}")


class NumericDomainError(ValueError):
    """The original positive inputs cannot be represented by the numeric rate path."""


def finite_inputs(inputs):
    v = list(map(float, inputs))
    if len(v) != 5 or not all(math.isfinite(x) and x >= 0 for x in v) or v[1] > v[2]:
        raise ValueError("invalid original P/gains/QoS")
    if not all(math.isfinite(v[0] * x) for x in v[1:3]):
        raise ValueError("received SNR overflow")
    if any(v[0] > 0 and gain > 0 and v[0] * gain == 0 for gain in v[1:3]):
        raise NumericDomainError("positive received-product underflow; numeric domain unsupported")
    return v


def rates(inputs, a):
    P, gw, gs, _, _ = finite_inputs(inputs)
    if not math.isfinite(a) or not 0 <= a <= 1:
        raise ValueError("illegal split")
    # Explicit transmitted powers and receiver noise/interference, both decoding sites.
    received_w, received_s = P * gw, P * gs
    # Evaluate the approved received-power equations with normalized noise one.
    weak_w, weak_s = (1 - a) * received_w, (1 - a) * received_s
    strong_w, strong_s = a * received_w, a * received_s
    ww, ws, ss = weak_w / (1 + strong_w), weak_s / (1 + strong_s), strong_s
    rw, cw, rs = (math.log1p(v) / math.log(2) for v in (ww, ws, ss))
    return dict(zip(FIELDS, (ww, ws, ss, rw, cw, min(rw, cw), rs, min(rw, cw) + rs)))


def oma(inputs):
    P, gw, gs, qw, qs = finite_inputs(inputs)
    rw, rs = (math.log1p(P * g) / (2 * math.log(2)) for g in (gw, gs))
    return dict(
        oma_rw=rw, oma_rs=rs, oma_sum=rw + rs, oma_residual_w=rw - qw, oma_residual_s=rs - qs
    )


def bracket(predicate, increasing, exact=False):
    z, o = (Fraction(0), Fraction(1)) if exact else (0.0, 1.0)
    if predicate(z):
        if increasing:
            return z, z
    elif not increasing:
        return None
    if predicate(o):
        if not increasing:
            return o, o
    elif increasing:
        return None
    lo, hi = z, o
    for _ in range(ROOT_CAP):
        m = (lo + hi) / 2
        if m == lo or m == hi:
            break
        if predicate(m) == increasing:
            hi = m
        else:
            lo = m
        if hi - lo <= SPLIT:
            break
    return lo, hi


def exact_residuals(inputs):
    P, gw, gs, qw, qs = finite_inputs(inputs)
    if not (qw.is_integer() and qs.is_integer() and max(qw, qs) <= 1024):
        return None
    p, w, s = map(Fraction, (P, gw, gs))
    A, B = p * w, p * s
    tw, ts = 2 ** int(qw) - 1, 2 ** int(qs) - 1

    # Original constraints multiplied by their strictly positive denominators.
    def residual(a):
        return ((1 - a) * A - tw * (1 + a * A), (1 - a) * B - tw * (1 + a * B), a * B - ts)

    return residual


def affine_crossing(f, increasing):
    """Exact affine interpolation only after full-domain monotone bracket."""
    br = bracket(lambda a: f(a) >= 0, increasing, True)
    if br is None:
        return None
    if br[0] == br[1]:
        return br[0]
    y0, y1 = f(Fraction(0)), f(Fraction(1))
    root = -y0 / (y1 - y0)
    if not br[0] <= root <= br[1]:
        raise ValueError("rational root outside original bracket")
    return root


def noma_adjudicate(inputs):
    try:
        v = finite_inputs(inputs)
    except NumericDomainError as exc:
        return dict(
            status="unresolved",
            certificate="numeric-domain-unsupported",
            reason=str(exc),
            numeric_domain=False,
            low=None,
            high=None,
        )
    if (v[0] * v[1] == 0 and v[3] > 0) or (v[0] * v[2] == 0 and v[4] > 0):
        return dict(status="infeasible", certificate="exact-zero-capacity", low=None, high=None)
    if v[3] == 0 and v[4] == 0:
        return dict(
            status="feasible", certificate="exact-zero-targets", low=0.0, high=1.0, singleton=False
        )
    exact = exact_residuals(v)
    if exact:
        bounds = [affine_crossing(lambda a, k=k: exact(a)[k], k == 2) for k in range(3)]
        if any(x is None for x in bounds):
            return dict(status="infeasible", certificate="original-Fraction", low=None, high=None)
        low, high = bounds[2], min(bounds[:2])
        status = "feasible" if low <= high else "infeasible"
        return dict(
            status=status,
            certificate="original-Fraction",
            low=float(low),
            high=float(high),
            exact_low=str(low),
            exact_high=str(high),
            singleton=low == high,
        )
    qw, qs = v[3:]
    # Check maximum endpoint capacities with declared rate ambiguity band.
    r0, r1 = rates(v, 0.0), rates(v, 1.0)
    if min(r0["rw_site"], r0["cw_at_s"]) < qw - RATE or r1["rs"] < qs - RATE:
        return dict(status="infeasible", certificate="capacity-separated", low=None, high=None)
    bw = bracket(lambda a: rates(v, float(a))["rw"] >= qw, False)
    bs = bracket(lambda a: rates(v, float(a))["rs"] >= qs, True)
    if bw is None or bs is None:
        return dict(status="unresolved", certificate="capacity-boundary", low=None, high=None)
    if bs[0] > bw[1]:
        # Disjoint approximate roots must be separated in original rates too.
        m = (bs[0] + bw[1]) / 2
        r = rates(v, m)
        if r["rw"] < qw - RATE and r["rs"] < qs - RATE:
            return dict(status="infeasible", certificate="bracket-separated", low=bs[0], high=bw[1])
        return dict(status="unresolved", certificate="rate-boundary", low=bs[0], high=bw[1])
    if bs[1] <= bw[0]:
        if bw[0] - bs[1] <= SPLIT:
            return dict(
                status="unresolved",
                certificate="uncertified-narrow-noninteger-domain",
                low=bs[1],
                high=bw[0],
                lower_bracket=list(bs),
                upper_bracket=list(bw),
            )
        return dict(
            status="feasible",
            certificate="original-monotone-brackets",
            low=bs[1],
            high=bw[0],
            lower_bracket=list(bs),
            upper_bracket=list(bw),
            singleton=False,
        )
    return dict(status="unresolved", certificate="overlapping-root-brackets", low=bs[0], high=bw[1])


def oma_adjudicate(inputs):
    try:
        v = finite_inputs(inputs)
    except NumericDomainError:
        return "unresolved"
    if (v[0] * v[1] == 0 and v[3] > 0) or (v[0] * v[2] == 0 and v[4] > 0):
        return "infeasible"
    d = oma(v)
    rr = [d["oma_residual_w"], d["oma_residual_s"]]
    if min(rr) < -RATE:
        return "infeasible"
    # Exactly zero target at exactly zero capacity is an elementary exact branch.
    if all(v[k] == 0 or rr[k - 3] > RATE for k in (3, 4)):
        return "feasible"
    p, w, s = map(Fraction, v[:3])
    checks = []
    for gain, q in zip((w, s), v[3:]):
        if q.is_integer() and q <= 512:
            checks.append(p * gain >= 2 ** (2 * int(q)) - 1)
        elif abs(d["oma_rw" if len(checks) == 0 else "oma_rs"] - q) <= RATE:
            return "unresolved"
        else:
            checks.append(True)
    return "feasible" if all(checks) else "infeasible"


def seeded(seed, n):
    g = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 0])))
    return np.sort(g.exponential(1.0, size=(n, 2)), axis=1)


class Audit:
    def __init__(self):
        self.errors = []
        self.counts = {}
        self.ambiguities = []
        self.diagnostics = []
        self.diagnostic_counts = {}

    def error(self, field, actual, expected, row=None):
        self.counts[field] = self.counts.get(field, 0) + 1
        if len(self.errors) < 2000:
            self.errors.append(
                dict(field=field, actual=str(actual), expected=str(expected), row=row)
            )

    def eq(self, field, actual, expected, row=None):
        if actual != expected:
            self.error(field, actual, expected, row)

    def close(self, field, actual, expected, tol=RATE, row=None):
        a, b = float(actual), float(expected)
        # NaN is allowed only as the explicitly expected undefined mask.
        if math.isnan(b):
            if not math.isnan(a):
                self.error(field, a, "undefined", row)
        elif not math.isfinite(a) or not math.isfinite(b) or abs(a - b) > tol:
            self.error(field, a, b, row)

    def diagnostic(self, field, actual, expected, row=None, unit="dimensionless"):
        self.diagnostic_counts[field] = self.diagnostic_counts.get(field, 0) + 1
        if len(self.diagnostics) < 2000:
            self.diagnostics.append(
                dict(
                    field=field,
                    actual=str(actual),
                    expected=str(expected),
                    residual=str(float(actual) - float(expected)),
                    unit=unit,
                    row=row,
                )
            )

    def sinr(self, field, actual, expected, row=None, rate=RATE):
        a, b = float(actual), float(expected)
        if math.isnan(b):
            self.close(field, a, b, 0.0, row)
            return
        if not math.isfinite(a) or a < 0 or not math.isfinite(b) or b < 0:
            self.error(field, a, b, row)
            return
        if a != b:
            self.diagnostic(field, a, b, row)
        self.close(
            field + ".implied_rate",
            math.log1p(a) / math.log(2),
            math.log1p(b) / math.log(2),
            rate,
            row,
        )

    def ok(self):
        return not self.counts


@dataclass
class Moments:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def add(self, x):
        if not math.isfinite(x):
            raise ValueError("nonfinite statistical sample")
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (x - self.mean)

    def summary(self, deterministic=False):
        if self.n == 0:
            return dict(
                n=0,
                mean=None,
                variance=None,
                ci95=None,
                halfwidth=None,
                relative_halfwidth=None,
                precision_met=False,
            )
        variance = self.m2 / (self.n - 1) if self.n >= 2 else None
        h = (
            float(t.ppf(0.975, self.n - 1)) * math.sqrt(variance / self.n)
            if self.n >= 2 and not deterministic
            else None
        )
        relative = h / abs(self.mean) if h is not None and self.mean != 0 else None
        return dict(
            n=self.n,
            mean=self.mean,
            variance=variance,
            ci95=[self.mean - h, self.mean + h] if h is not None else None,
            halfwidth=h,
            relative_halfwidth=relative,
            precision_met=relative is not None and relative <= 0.01,
        )


def binomial(k, n):
    if type(k) is not int or type(n) is not int or not 0 <= k <= n:
        raise ValueError("invalid binomial denominator")
    if n == 0:
        return dict(
            events=k,
            denominator=n,
            estimate=None,
            ci95=None,
            minimum_events_met=False,
            zero_event_upper_bound=None,
        )
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return dict(
        events=k,
        denominator=n,
        estimate=k / n,
        ci95=[lo, hi],
        minimum_events_met=k >= 100,
        zero_event_upper_bound=hi if k == 0 else None,
    )


def reference(P):
    def f(x):
        return math.exp(x) * float(exp1(x))

    r2, r1 = f(2 / P), f(1 / P)
    return dict(
        weak=r2 / (2 * math.log(2)), strong=(2 * r1 - r2) / (2 * math.log(2)), sum=r1 / math.log(2)
    )


def ablations(inputs):
    P, gw, gs, qw, qs = finite_inputs(inputs)
    fixed = rates(inputs, 0.25)
    ff = fixed["rw"] >= qw and fixed["rs"] >= qs
    # Per-row fixed 101-point arrays keep the exhaustive grid bounded while
    # eliminating 101 temporary Python rate dictionaries from every row.
    splits = np.arange(101, dtype=float) / 100
    A, B = P * gw, P * gs
    weak_w = (1 - splits) * A / (1 + splits * A)
    weak_s = (1 - splits) * B / (1 + splits * B)
    rw = np.minimum(np.log1p(weak_w), np.log1p(weak_s)) / math.log(2)
    rs = np.log1p(splits * B) / math.log(2)
    feasible = (rw >= qw) & (rs >= qs)
    sums = rw + rs
    found = bool(np.any(feasible))
    best = float(np.max(sums[feasible])) if found else float("nan")
    ties = splits[feasible & (np.abs(sums - best) <= OBJECTIVE)].tolist() if found else []
    return dict(
        fixed_feasible=float(ff),
        fixed_sum=fixed["sum_rate"] if ff else float("nan"),
        grid_found_feasible=float(found),
        grid_sum=best,
        grid_ties=ties,
    )


def negative_pair(value):
    return math.isfinite(float(value)) and float(value) < -RATE


def category(ns, os):
    if "unresolved" in (ns, os):
        return "unresolved"
    return "n" + str(int(ns == "feasible")) + str(int(os == "feasible"))


def check_candidate_flags(raw, computed, inputs, row_id, audit):
    """Check serialized diagnostics and independently recomputed predicates separately.

    Only binary64 roundoff can explain a diagnostic sign disagreement. This is
    not a feasibility certificate or a change to the approved rate tolerance.
    """
    stored = [number(raw["candidate_" + k]) for k in ("rw", "rs")]
    actual = [computed[k] for k in ("rw", "rs")]
    targets = inputs[3:]
    predicates = (
        ("candidate_constraints_pass", lambda r: all(x >= q for x, q in zip(r, targets))),
        (
            "candidate_within_rate_tolerance",
            lambda r: all(x >= q - RATE for x, q in zip(r, targets)),
        ),
        ("candidate_violation", lambda r: min(x - q for x, q in zip(r, targets)) < -RATE),
    )
    for field, predicate in predicates:
        reported = boolean(raw[field])
        expected_serialized = predicate(stored)
        expected_independent = predicate(actual)
        audit.eq(field, reported, expected_serialized, row_id)
        if expected_serialized != expected_independent:
            # Engineering roundoff in each rate, distinct from a scientific band.
            roundoff_only = all(
                math.isfinite(x) and abs(x - y) <= 64 * math.ulp(max(1.0, abs(x), abs(y), abs(q)))
                for x, y, q in zip(stored, actual, targets)
            )
            if roundoff_only:
                audit.diagnostic(
                    field + ".roundoff",
                    float(expected_serialized),
                    float(expected_independent),
                    row_id,
                )
            else:
                audit.error(field + ".independent", reported, expected_independent, row_id)


def check_row(raw, metric, expected_inputs, expected_case, row_id, audit):
    inputs = finite_inputs([number(raw[k]) for k in ("P", "gw", "gs", "qw", "qs")])
    for k, x, y in zip(("P", "gw", "gs", "qw", "qs"), inputs, expected_inputs):
        audit.close(k, x, y, 0.0, row_id)
    audit.eq("row", raw["row"], str(row_id), row_id)
    audit.eq("case_id", raw.get("case_id", ""), expected_case, row_id)
    for k in METRIC_COLUMNS:
        audit.close("metrics." + k, metric[k], raw[k], 0.0, row_id)
    for k in ("A", "B"):
        audit.close(k, raw[k], inputs[0] * inputs[1 if k == "A" else 2], 0.0, row_id)
    od = oma(inputs)
    for k, v in od.items():
        audit.close(k, raw[k], v, RATE, row_id)
    ns = noma_adjudicate(inputs)
    os = oma_adjudicate(inputs)
    audit.eq("numeric_domain", boolean(raw["numeric_domain"]), True, row_id)
    certificates = {
        "none",
        "exact-zero",
        "exact-zero-weak",
        "exact-zero-strong",
        "exact-rational",
        "binary64-separated",
        "binary64-capacity-separated",
    }
    for field in ("certificate", "oma_certificate"):
        if raw[field] not in certificates:
            audit.error(field, raw[field], "declared certificate kind", row_id)
    for field, stored_status in (
        ("certificate", raw["status"]),
        ("oma_certificate", raw["oma_status"]),
    ):
        audit.eq(
            field + ".none_status", raw[field] == "none", stored_status == "unresolved", row_id
        )
    for label, s, b in (("noma", ns["status"], raw["status"]), ("oma", os, raw["oma_status"])):
        if s == "unresolved":
            audit.ambiguities.append(
                dict(
                    row=row_id,
                    method=label,
                    independent_status=s,
                    stored_status=b,
                    reason=ns.get("certificate") if label == "noma" else "rate-boundary",
                )
            )
        else:
            audit.eq(label + ".status", b, s, row_id)
    # Stored ambiguity is retained; independent inability never endorses a stored resolved bit.
    for k, s in (("feasible", raw["status"]), ("oma_feasible", raw["oma_status"])):
        if s not in {"feasible", "infeasible", "unresolved"}:
            audit.error(k + ".status", s, "valid status", row_id)
        audit.close(
            k, raw[k], float("nan") if s == "unresolved" else float(s == "feasible"), 0.0, row_id
        )

    # Adjudicate recorded interval boundaries as original affine constraint crossings.
    # These are diagnostic boundary checks, never the feasibility classifier.
    p, w, s, qw, qs = inputs
    A = p * w
    B = p * s
    for field, snr, q, increasing in (
        ("interval_lower", B, qs, True),
        ("interval_upper", A, qw, False),
    ):
        bound = number(raw[field])
        if not math.isfinite(bound):
            audit.error(field, bound, "finite diagnostic bound", row_id)
            continue
        if snr == 0:
            expected_bound = 0.0 if increasing else 1.0
        elif q == 0:
            expected_bound = 0.0 if increasing else 1.0
        elif q.is_integer() and q <= 1024:
            x = Fraction(p) * Fraction(s if increasing else w)
            target = 2 ** int(q) - 1

            def affine(a):
                return a * x - target if increasing else (1 - a) * x - target * (1 + a * x)

            f0, f1 = affine(Fraction(0)), affine(Fraction(1))
            cross = -f0 / (f1 - f0)
            expected_bound = float(cross) if increasing else min(1.0, float(cross))
        else:
            target = math.expm1(q * math.log(2))

            # Derive the slope from the original affine constraint directly.
            # Subtracting endpoint residuals cancels when the channel is small.
            cross = target / snr if increasing else (snr - target) / (snr * (1 + target))
            expected_bound = cross if increasing else min(1.0, cross)
        label = field + ".original_crossing"
        # Crossings outside [0,1] are diagnostics, not admissible power splits.
        # Preserve their side of the domain and reject material corruption, but
        # retain binary64 roundoff separately when one ULP exceeds SPLIT.
        # All physical-domain, exact-integer and feasibility checks keep SPLIT.
        same_outside = (bound < 0 and expected_bound < 0) or (bound > 1 and expected_bound > 1)
        diagnostic_roundoff = (
            not q.is_integer()
            and snr > 0
            and same_outside
            and math.isfinite(expected_bound)
            and abs(bound - expected_bound) > SPLIT
            and abs(bound - expected_bound)
            <= 64 * math.ulp(max(1.0, abs(bound), abs(expected_bound)))
        )
        if diagnostic_roundoff:
            audit.diagnostic(label + ".roundoff", bound, expected_bound, row_id, unit="split")
        else:
            audit.close(label, bound, expected_bound, SPLIT, row_id)
    if ns["low"] is not None and ns["high"] is not None:
        audit.eq(
            "boundary_flag",
            boolean(raw["boundary_flag"]),
            abs(ns["high"] - ns["low"]) <= SPLIT,
            row_id,
        )
    audit.eq(
        "oma_boundary_flag",
        boolean(raw["oma_boundary_flag"]),
        any(
            q > 0 and abs(od[k]) <= RATE
            for q, k in zip(inputs[3:], ("oma_residual_w", "oma_residual_s"))
        ),
        row_id,
    )
    if raw["certificate"] == "exact-rational" and exact_residuals(inputs) is None:
        audit.error("certificate", raw["certificate"], "integer original certificate", row_id)
    if raw["oma_certificate"] == "exact-rational" and not all(q.is_integer() for q in inputs[3:]):
        audit.error(
            "oma_certificate", raw["oma_certificate"], "integer original OMA certificate", row_id
        )
    cat = category(raw["status"], raw["oma_status"])
    audit.eq("category", raw["category"], cat, row_id)
    if ns["status"] != "unresolved" and os != "unresolved":
        audit.eq("independent.category", raw["category"], category(ns["status"], os), row_id)
    feasible = raw["status"] == "feasible"
    for prefix, split in (("", number(raw["a_star"])), ("candidate_", number(raw["candidate_a"]))):
        present = math.isfinite(split)
        accepted = prefix == "" and feasible
        attempted = prefix == "candidate_" and present
        if accepted or attempted:
            if not present or not 0 <= split <= 1:
                audit.error(prefix + "split", split, "[0,1]", row_id)
                continue
            rd = rates(inputs, split)
            for k, x in rd.items():
                if k.startswith("gamma_"):
                    audit.sinr(prefix + k, raw[prefix + k], x, row_id)
                else:
                    audit.close(
                        prefix + k,
                        raw[prefix + k],
                        x,
                        OBJECTIVE if k == "sum_rate" else RATE,
                        row_id,
                    )
        else:
            audit.close(prefix + "split", split, float("nan"), 0.0, row_id)
            for k in FIELDS:
                audit.close(prefix + k, raw[prefix + k], float("nan"), 0.0, row_id)
    candidate = number(raw["candidate_a"])
    if math.isfinite(candidate) and 0 <= candidate <= 1:
        cr = rates(inputs, candidate)
        check_candidate_flags(raw, cr, inputs, row_id, audit)
    else:
        for k in (
            "candidate_constraints_pass",
            "candidate_within_rate_tolerance",
            "candidate_violation",
        ):
            audit.eq(k, boolean(raw[k]), False, row_id)
    if feasible and math.isfinite(number(raw["a_star"])) and 0 <= number(raw["a_star"]) <= 1:
        rd = rates(inputs, number(raw["a_star"]))
        for k, v in (
            ("residual_w", rd["rw"] - inputs[3]),
            ("residual_s", rd["rs"] - inputs[4]),
            ("sic_residual", rd["cw_at_s"] - rd["rw"]),
        ):
            audit.close(k, raw[k], v, RATE, row_id)
        for k in ("residual_w", "residual_s", "sic_residual"):
            if number(raw[k]) < -RATE:
                audit.error("original_constraint." + k, raw[k], ">=-rate_tolerance", row_id)
        audit.close("candidate_a.identity", raw["candidate_a"], raw["a_star"], 0.0, row_id)
        if ns["status"] == "feasible" and ns["high"] is not None:
            # Compare the chosen endpoint representation, not exact Fraction(a_star)
            # membership: a certified singleton may need a rounded binary64 split.
            audit.close("selected_endpoint", raw["a_star"], ns["high"], SPLIT, row_id)
            audit.close(
                "optimal_objective",
                raw["sum_rate"],
                rates(inputs, ns["high"])["sum_rate"],
                OBJECTIVE,
                row_id,
            )
            if ns.get("upper_bracket"):
                audit.close(
                    "interval_upper", raw["interval_upper"], ns["upper_bracket"][1], SPLIT, row_id
                )
            else:
                audit.close("interval_upper", raw["interval_upper"], ns["high"], SPLIT, row_id)
            audit.close("interval_lower", raw["interval_lower"], ns["low"], SPLIT, row_id)
        for field, target in (("rw_site", inputs[3]), ("cw_at_s", inputs[3]), ("rs", inputs[4])):
            if rd[field] < target - RATE:
                audit.error("selected_original_constraint." + field, rd[field], target, row_id)
        weak_expected = inputs[3] if inputs[0] > 0 and inputs[1] > 0 else 0.0
        audit.close("weak_target_activation", rd["rw_site"], weak_expected, RATE, row_id)
        audit.eq("numeric_domain", boolean(raw["numeric_domain"]), True, row_id)
        if raw["exact_split"]:
            f = Fraction(raw["exact_split"])
            ex = exact_residuals(inputs)
            audit.close("exact_split.float", float(f), raw["a_star"], SPLIT, row_id)
            if not ex or min(ex(f)) < 0:
                audit.error(
                    "exact_split.witness",
                    raw["exact_split"],
                    "exact original feasible witness",
                    row_id,
                )
        singleton = bool(ns.get("singleton", False))
        if ns["status"] == "feasible":
            audit.eq("singleton", boolean(raw["singleton"]), singleton, row_id)
            # Common nonnegative P gives exact product equality iff P=0 or gw=gs.
            # Rounded received products can collapse even when exact B>A.
            unique = (inputs[0] > 0 and inputs[1] != inputs[2]) or singleton
            audit.eq("optimizer_unique", boolean(raw["optimizer_unique"]), unique, row_id)
            audit.eq("nonunique", boolean(raw["nonunique"]), not unique, row_id)
    else:
        for k in ("residual_w", "residual_s", "sic_residual"):
            audit.close(k, raw[k], float("nan"), 0.0, row_id)
        for k in ("singleton", "optimizer_unique", "nonunique"):
            audit.eq(k, boolean(raw[k]), False, row_id)
    paired = (
        rates(inputs, number(raw["a_star"]))["sum_rate"] - od["oma_sum"]
        if cat == "n11" and math.isfinite(number(raw["a_star"])) and 0 <= number(raw["a_star"]) <= 1
        else float("nan")
    )
    audit.close("paired_difference", raw["paired_difference"], paired, RATE, row_id)
    if cat == "n11" and (negative_pair(paired) or negative_pair(raw["paired_difference"])):
        audit.error(
            "negative_paired_difference", raw["paired_difference"], ">=-rate_tolerance", row_id
        )
    ab = ablations(inputs)
    for k in ("fixed_feasible", "fixed_sum", "grid_found_feasible", "grid_sum"):
        audit.close(k, raw[k], ab[k], OBJECTIVE if k.endswith("sum") else 0.0, row_id)
    ga = number(raw["grid_a"])
    if ab["grid_found_feasible"]:
        if not math.isfinite(ga) or not 0 <= ga <= 1:
            audit.error("grid_a", ga, "split in [0,1] with an integer grid index", row_id)
        else:
            # Recover the discrete index, then validate its representation.
            # 0.69 and 0.6900000000000001 both represent index 69.
            index = round(ga * 100)
            canonical = index / 100
            maximizing_indices = {round(a * 100) for a in ab["grid_ties"]}
            if (
                type(index) is not int
                or not 0 <= index <= 100
                or abs(ga - canonical) > SPLIT
                or index not in maximizing_indices
            ):
                audit.error("grid_a", ga, "feasible maximizing integer grid index", row_id)
            recorded_grid = rates(inputs, ga)
            for field, target in (
                ("rw_site", inputs[3]),
                ("cw_at_s", inputs[3]),
                ("rs", inputs[4]),
            ):
                if recorded_grid[field] < target - RATE:
                    audit.error(
                        "grid.recorded_constraint." + field, recorded_grid[field], target, row_id
                    )
            audit.close(
                "grid.recorded_objective",
                recorded_grid["sum_rate"],
                ab["grid_sum"],
                OBJECTIVE,
                row_id,
            )
            audit.close(
                "grid.recorded_sum", raw["grid_sum"], recorded_grid["sum_rate"], OBJECTIVE, row_id
            )
    else:
        audit.close("grid_a", ga, float("nan"), 0.0, row_id)
    if feasible and math.isfinite(number(raw["a_star"])) and 0 <= number(raw["a_star"]) <= 1:
        selected_sum = rates(inputs, number(raw["a_star"]))["sum_rate"]
        for kind, flag in (("fixed", "fixed_feasible"), ("grid", "grid_found_feasible")):
            if ab[flag] == 1:
                loss = selected_sum - ab[kind + "_sum"]
                if loss < -OBJECTIVE:
                    audit.error(
                        "ablation." + kind + ".negative_loss",
                        loss,
                        ">=-objective_tolerance",
                        row_id,
                    )
    return inputs, ns, os, cat, paired, od, ab


def check_jobs(manifests, spec):
    planned = {(s["id"], seed): s for s in spec["scenarios"] for seed in s["seeds"]}
    actual = [(m["scenario"], m["seeds"][0]) for m in manifests if len(m["seeds"]) == 1]
    if (
        len(planned) != 145
        or len(actual) != 145
        or len(set(actual)) != 145
        or set(actual) != set(planned)
    ):
        raise ValueError("missing/duplicate/unplanned/empty jobs")
    for m in manifests:
        s = planned[(m["scenario"], m["seeds"][0])]
        if m["params"] != s["params"]:
            raise ValueError("job parameter mismatch")
    return planned
