"""Shared pinned oracle replay; this is NOT a third independent optimizer."""

from __future__ import annotations

import importlib.util
import math

from independent import OBJECTIVE, RATE, SPLIT, oma, rates


def load_shared(path):
    spec = importlib.util.spec_from_file_location("supplement_shared_pinned_oracle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.solve


def recursive_compare(
    audit, label, stored, new, row, rate=RATE, split=SPLIT, objective=OBJECTIVE, undefined=False
):
    if isinstance(new, dict):
        audit.eq(label + ".schema", set(stored), set(new), row)
        for k in new:
            if k in stored:
                recursive_compare(
                    audit,
                    label + "." + k,
                    stored[k],
                    new[k],
                    row,
                    rate,
                    split,
                    objective,
                    undefined,
                )
    elif isinstance(new, (int, float)) and not isinstance(new, bool):
        if isinstance(new, int):
            audit.eq(label, stored, new, row)
        else:
            if math.isnan(new):
                field = label.rsplit(".", 1)[-1]
                permitted = {
                    "feasible",
                    "a_star",
                    "candidate_a",
                    "rw",
                    "rs",
                    "sum_rate",
                    "residual_w",
                    "residual_s",
                    "sic_residual",
                    "objective_upper_bound",
                    "objective_gap_bound",
                    "inner_lower",
                    "inner_upper",
                    "outer_lower",
                    "outer_upper",
                }
                if undefined and field in permitted:
                    audit.eq(label, stored, None, row)
                else:
                    audit.error(label, "NaN", "finite or declared undefined mask", row)
                return
            # Split/bound fields use split tolerance; objective fields use objective tolerance.
            tol = (
                split
                if any(x in label for x in ("a_star", "candidate_a", "inner_", "outer_"))
                else objective
                if any(x in label for x in ("sum_rate", "objective_"))
                else rate
            )
            if "gamma_" in label and stored is not None:
                audit.sinr(label, stored, new, row, rate)
                return
            if new is None or stored is None:
                audit.eq(label, stored, new, row)
            else:
                audit.close(label, stored, new, tol, row)
    else:
        audit.eq(label, stored, new, row)


def check_oracle_original(audit, label, result, inputs, row):
    # Candidate diagnostics remain meaningful even if a final optimum is undefined.
    candidate = result.get("candidate_a")
    if candidate is not None:
        if not math.isfinite(candidate) or not 0 <= candidate <= 1:
            audit.error(label + ".candidate_a", candidate, "[0,1]", row)
            return
        cr = rates(inputs, candidate)
        for k, v in cr.items():
            field = "candidate_" + k
            if field in result:
                if k.startswith("gamma_"):
                    audit.sinr(label + "." + field, result[field], v, row, result["rate_tolerance"])
                else:
                    audit.close(
                        label + "." + field,
                        result[field],
                        v,
                        result["objective_tolerance"]
                        if k == "sum_rate"
                        else result["rate_tolerance"],
                        row,
                    )
    status = result["status"]
    audit.eq(
        label + ".status_domain", status in {"feasible", "infeasible", "unresolved"}, True, row
    )
    if status == "feasible":
        split = result["a_star"]
        if split is None or not math.isfinite(split) or not 0 <= split <= 1:
            audit.error(label + ".split", split, "[0,1]", row)
            return
        r = rates(inputs, split)
        for k, v in r.items():
            if k in result:
                if k.startswith("gamma_"):
                    audit.sinr(label + "." + k, result[k], v, row, result["rate_tolerance"])
                else:
                    audit.close(
                        label + "." + k,
                        result[k],
                        v,
                        result["objective_tolerance"]
                        if k == "sum_rate"
                        else result["rate_tolerance"],
                        row,
                    )
        for k, v in oma(inputs).items():
            if k in result:
                audit.close(label + "." + k, result[k], v, result["rate_tolerance"], row)
        if min(r["rw"] - inputs[3], r["rs"] - inputs[4]) < -result["rate_tolerance"]:
            audit.error(label + ".original_constraints", split, "QoS witness", row)


def replay_job(checks, raw_rows, params, solve, audit):
    n = params["oracle_rows"]
    tighter = params["sensitivity_rows"]
    ids = [c["row"] for c in checks]
    audit.eq("oracle.coverage", ids, list(range(n)))
    if len(raw_rows) < n:
        raise ValueError("missing raw replay row")
    base_count = tight_count = 0
    statuses = {}
    for c in checks:
        row = c["row"]
        if type(row) is not int or not 0 <= row < n:
            audit.error("oracle.row", row, "planned row")
            continue
        raw = raw_rows[row]
        inputs = [float(raw[k]) for k in ("P", "gw", "gs", "qw", "qs")]
        audit.eq("oracle.inputs", c["inputs"], inputs, row)
        audit.eq("oracle.analytic_status", c["analytic_status"], raw["status"], row)
        expected = None if not math.isfinite(float(raw["sum_rate"])) else float(raw["sum_rate"])
        if expected is None:
            audit.eq("oracle.analytic_sum", c["analytic_sum"], None, row)
        else:
            audit.close("oracle.analytic_sum", c["analytic_sum"], expected, OBJECTIVE, row)
        for key, factor in (("oracle", 1), ("tighter_oracle", 10)):
            if factor == 10 and row >= tighter:
                audit.eq("oracle.unplanned_tighter", key in c, False, row)
                continue
            if key not in c:
                audit.error("oracle.missing." + key, None, "required replay", row)
                continue
            kwargs = {
                k: params[k] / factor
                for k in ("rate_tolerance", "split_tolerance", "objective_tolerance")
            }
            kwargs.update(max_root_iterations=96, max_optimizer_iterations=256)
            regenerated = solve(*inputs, **kwargs)
            recursive_compare(
                audit,
                key,
                c[key],
                regenerated,
                row,
                kwargs["rate_tolerance"],
                kwargs["split_tolerance"],
                kwargs["objective_tolerance"],
                regenerated["status"] != "feasible",
            )
            check_oracle_original(audit, key, c[key], inputs, row)
            for k, v in kwargs.items():
                audit.eq(key + "." + k, c[key].get(k), v, row)
            statuses[regenerated["status"]] = statuses.get(regenerated["status"], 0) + 1
            if factor == 1:
                base_count += 1
            else:
                tight_count += 1
    audit.eq("oracle.base_count", base_count, n)
    audit.eq("oracle.tight_count", tight_count, tighter)
    return dict(base=base_count, tighter=tight_count, statuses=statuses)
