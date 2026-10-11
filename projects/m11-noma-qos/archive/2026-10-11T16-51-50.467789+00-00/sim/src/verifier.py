"""Pinned P6 recomputation; must be reviewed independently before P6 execution.

Uses original rates, a full-domain constraint bracket, and the distinct scalar
oracle. It does not import the analytic metric implementation. This module is
prepared at P5 so subsequent verification never changes locked run inputs.
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
import oracle

from lab.io import load, save
from lab.simulation import manifest_output, verify_manifest
from lab.verification import average_ci


def rates(P, gw, gs, a):
    # Original transmit powers and received interference, independently written.
    weak_power, strong_power = P * (1 - a), P * a
    weak_sinr = weak_power * gw / (1 + strong_power * gw)
    decoding_sinr = weak_power * gs / (1 + strong_power * gs)
    strong_sinr = strong_power * gs
    return tuple(np.log1p(x) / np.log(2) for x in (weak_sinr, decoding_sinr, strong_sinr))


def bracket(P, gw, gs, qw, qs):
    n = len(gw)
    lower_lo, lower_hi = np.zeros(n), np.ones(n)
    upper_lo, upper_hi = np.zeros(n), np.ones(n)
    for _ in range(48):
        m = (lower_lo + lower_hi) / 2
        strong_ok = rates(P, gw, gs, m)[2] >= qs
        lower_hi = np.where(strong_ok, m, lower_hi)
        lower_lo = np.where(strong_ok, lower_lo, m)
        m = (upper_lo + upper_hi) / 2
        w, s, _ = rates(P, gw, gs, m)
        weak_ok = np.minimum(w, s) >= qw
        upper_lo = np.where(weak_ok, m, upper_lo)
        upper_hi = np.where(weak_ok, upper_hi, m)
    min_lower = np.where(qs == 0, 0, lower_lo)
    max_upper = np.where(qw == 0, 1, upper_hi)
    endpoint_w = rates(P, gw, gs, np.zeros(n))[0]
    endpoint_s = rates(P, gw, gs, np.ones(n))[2]
    possible = (endpoint_w >= qw) & (endpoint_s >= qs)
    margin = max_upper - min_lower
    return possible, margin


def exact_constraints(values, split):
    P, gw, gs, qw, qs = values
    if not float(qw).is_integer() or not float(qs).is_integer() or not split:
        return None
    a = Fraction(str(split))
    P, gw, gs = map(lambda x: Fraction(float(x)), (P, gw, gs))
    weak = (1 - a) * P * gw / (1 + a * P * gw)
    decode = (1 - a) * P * gs / (1 + a * P * gs)
    strong = a * P * gs
    return 0 <= a <= 1 and min(weak, decode) >= 2 ** int(qw) - 1 and strong >= 2 ** int(qs) - 1


def verify(project, output):
    output.mkdir(exist_ok=True, parents=True)
    counts = defaultdict(int)
    maxima = defaultdict(float)
    groups = defaultdict(list)
    evidence = []
    tighter_differences = []
    oracle_differences = []
    for mf in sorted((project / "results/runs").glob("*/manifest.json")):
        manifest = verify_manifest(project, load(mf))
        file = manifest_output(project, manifest, "channels.csv")
        d = np.genfromtxt(file, delimiter=",", names=True, dtype=None, encoding="utf-8")
        evidence.append(mf.relative_to(project).as_posix())
        P, gw, gs, qw, qs = [d[k] for k in ("P", "gw", "gs", "qw", "qs")]
        feasible = d["status"] == "feasible"
        a = np.where(feasible, d["a_star"], 0)
        rw, decode, rs = rates(P, gw, gs, a)
        oma_w = np.log1p(P * gw) / np.log(2) / 2
        oma_s = np.log1p(P * gs) / np.log(2) / 2
        original_sum = np.minimum(rw, decode) + rs
        counts["rows"] += len(d)
        counts["unresolved"] += int(np.sum(d["category"] == "unresolved"))
        counts["sic_violations"] += int(np.sum(feasible & (decode < rw - 1e-9)))
        counts["constraint_violations"] += int(
            np.sum(feasible & ((rw < qw - 1e-9) | (rs < qs - 1e-9)))
        )
        if np.any(feasible):
            maxima["sum_recomputation_error"] = max(
                maxima["sum_recomputation_error"],
                float(np.max(np.abs(original_sum[feasible] - d["sum_rate"][feasible]))),
            )
        active = feasible & (P * gw > 0)
        if np.any(active):
            maxima["weak_activation_error"] = max(
                maxima["weak_activation_error"], float(np.max(np.abs(rw[active] - qw[active])))
            )
        maxima["oma_recomputation_error"] = max(
            maxima["oma_recomputation_error"], float(np.max(np.abs(oma_w + oma_s - d["oma_sum"])))
        )
        counts["oma_only"] += int(np.sum(d["category"] == "n01"))
        both = d["category"] == "n11"
        counts["negative_paired"] += int(np.sum(both & (original_sum - oma_w - oma_s < -1e-9)))
        possible, margin = bracket(P, gw, gs, qw, qs)
        separated = np.abs(margin) > 1e-9
        root_feasible = possible & (margin > 0)
        decided = d["status"] != "unresolved"
        counts["bracket_disagreements"] += int(
            np.sum(separated & decided & (root_feasible != feasible))
        )
        for j in np.flatnonzero(d["certificate"] == "exact-rational"):
            if feasible[j] and not exact_constraints(
                [x[j] for x in (P, gw, gs, qw, qs)], str(d["exact_split"][j])
            ):
                counts["exact_certificate_failures"] += 1
        for u, v in ((0, 0), (0, 1), (1, 0), (1, 1)):
            expected = (d["feasible"] == u) & (d["oma_feasible"] == v)
            counts["ledger_disagreements"] += int(np.sum(expected != (d["category"] == f"n{u}{v}")))
        counts["undefined_optimum_violations"] += int(
            np.sum(~feasible & np.isfinite(d["sum_rate"]))
        )
        if manifest.params["kind"] != "deterministic":
            groups[manifest.scenario].append(d)
        for checked in load(manifest_output(project, manifest, "oracle.json"))["checks"]:
            j = checked["row"]
            independently_repeated = oracle.solve(*checked["inputs"])
            old = checked["oracle"]
            counts["oracle_status_disagreements"] += int(
                independently_repeated["status"] != old["status"]
            )
            oracle_value = independently_repeated.get("sum_rate")
            if feasible[j] and oracle_value is not None and math.isfinite(oracle_value):
                oracle_differences.append(abs(float(d["sum_rate"][j]) - oracle_value))
            tighter = checked.get("tighter_oracle")
            if tighter and old.get("sum_rate") is not None and tighter.get("sum_rate") is not None:
                tighter_differences.append(abs(old["sum_rate"] - tighter["sum_rate"]))
    precision = {}
    for scenario, parts in groups.items():
        d = np.concatenate(parts)
        mask = d["category"] == "n11"
        precision[scenario] = {}
        for name in ("sum_rate", "oma_sum", "paired_difference"):
            values = d[name][mask]
            summary = average_ci(values) if len(values) >= 2 else None
            precision[scenario][name] = summary
    all_precision = all(
        v is not None and v["relative_halfwidth"] <= 0.01
        for s in precision.values()
        for v in s.values()
    )
    checks_boolean = {
        "independent-recomputation": maxima["sum_recomputation_error"] <= 1e-9
        and maxima["oma_recomputation_error"] <= 1e-9,
        "units": maxima["oma_recomputation_error"] <= 1e-9,
        "constraints": counts["constraint_violations"]
        == counts["sic_violations"]
        == counts["bracket_disagreements"]
        == counts["exact_certificate_failures"]
        == 0,
        "convergence": bool(oracle_differences)
        and max(oracle_differences) <= 1e-7
        and counts["oracle_status_disagreements"] == 0,
        "fairness": counts["oma_only"] == counts["negative_paired"] == 0,
        "statistical-precision": all_precision,
        "sensitivity": bool(tighter_differences) and max(tighter_differences) <= 1e-7,
        "ablations": all(
            (
                load(project / "results/statistics.json")["scenarios"][j]["ablations"][method][
                    "minimum_loss"
                ]
                or 0
            )
            >= -1e-7
            for j in range(len(load(project / "results/statistics.json")["scenarios"]))
            for method in ("fixed", "grid")
        ),
    }
    details = {
        "counts": dict(counts),
        "maxima": dict(maxima),
        "precision": precision,
        "maximum_oracle_difference": max(oracle_differences, default=None),
        "maximum_tighter_difference": max(tighter_differences, default=None),
        "limits": "Finite numerical checks; boundary unresolveds retained; no universal proof.",
    }
    save(output / "recomputation.json", details)
    receipt = (output / "recomputation.json").relative_to(project).as_posix()
    checks = {
        k: {"passed": bool(v), "evidence_paths": [receipt, *evidence]}
        for k, v in checks_boolean.items()
    }
    save(output / "checks.yaml", checks)
    outcomes = {
        "P1": counts["sic_violations"] == 0,
        "P2": checks_boolean["constraints"],
        "P3": checks_boolean["convergence"],
        "P4": maxima["weak_activation_error"] <= 1e-9,
        "P5": checks_boolean["fairness"],
        "P6": counts["ledger_disagreements"] == counts["undefined_optimum_violations"] == 0,
        "P7": checks_boolean["convergence"] and checks_boolean["sensitivity"],
    }
    save(
        output / "verification.yaml",
        [
            {
                "id": "V-" + key,
                "prediction_ref": key,
                "method": "Direct original-rate recomputation, full-domain constraint brackets and distinct oracle",
                "metric": "Numerical consistency under locked protocol",
                "value": None,
                "tolerance": {
                    "rate": 1e-9,
                    "objective": 1e-7,
                    "unresolved": "retained, no assertion",
                },
                "verdict": "PASS" if passed else "FAIL",
                "triage": None if passed else "implementation-bug",
                "evidence_paths": [receipt],
            }
            for key, passed in outcomes.items()
        ],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    verify(args.project.resolve(), args.output_dir.resolve())
