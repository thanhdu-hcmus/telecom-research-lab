"""Shared pinned oracle replay; this is NOT a third independent optimizer."""

from __future__ import annotations

import importlib.util
import math

from independent import FIELDS, OBJECTIVE, RATE, SPLIT, noma_adjudicate, oma, rates


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
        if label.rsplit(".", 1)[-1] == "feasible":
            audit.eq(label, stored, None if math.isnan(new) else new, row)
            return
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


def check_oracle_original(audit, label, result, inputs, row, policy=None):
    policy = policy or result
    rate_tolerance = policy["rate_tolerance"]
    objective_tolerance = policy["objective_tolerance"]
    status = result["status"]
    audit.eq(
        label + ".status_domain", status in {"feasible", "infeasible", "unresolved"}, True, row
    )
    expected_mask = {"feasible": 1.0, "infeasible": 0.0, "unresolved": None}.get(status)
    mask = result.get("feasible")
    audit.eq(label + ".feasible", mask, expected_mask, row)
    if isinstance(mask, bool):
        audit.error(label + ".feasible.type", mask, "numeric binary indicator or null", row)
    # Final fields describe an accepted optimum; candidate fields describe an attempt.
    for field in ("a_star", *FIELDS):
        if status != "feasible" and field in result:
            audit.eq(label + "." + field + ".mask", result[field], None, row)
    # Candidate diagnostics remain meaningful even if a final optimum is undefined.
    candidate = result.get("candidate_a")
    if candidate is None:
        for field in ("candidate_" + k for k in FIELDS):
            if field in result:
                audit.eq(label + "." + field + ".mask", result[field], None, row)
        for field in (
            "residual_w",
            "residual_s",
            "sic_residual",
            "objective_upper_bound",
            "objective_gap_bound",
        ):
            audit.eq(label + "." + field + ".mask", result.get(field), None, row)
    if candidate is not None:
        if not math.isfinite(candidate) or not 0 <= candidate <= 1:
            audit.error(label + ".candidate_a", candidate, "[0,1]", row)
            return
        cr = rates(inputs, candidate)
        for k, v in cr.items():
            field = "candidate_" + k
            if field not in result or result[field] is None:
                audit.error(label + "." + field + ".mask", result.get(field), "attempted rate", row)
            else:
                if k.startswith("gamma_"):
                    audit.sinr(label + "." + field, result[field], v, row, rate_tolerance)
                else:
                    audit.close(
                        label + "." + field,
                        result[field],
                        v,
                        objective_tolerance if k == "sum_rate" else rate_tolerance,
                        row,
                    )
        for field, value in (
            ("residual_w", cr["rw"] - inputs[3]),
            ("residual_s", cr["rs"] - inputs[4]),
            ("sic_residual", cr["cw_at_s"] - cr["rw"]),
        ):
            if result.get(field) is None:
                audit.error(label + "." + field + ".mask", None, "attempted residual", row)
            else:
                audit.close(label + "." + field, result[field], value, rate_tolerance, row)
    if status == "feasible":
        split = result["a_star"]
        if split is None or not math.isfinite(split) or not 0 <= split <= 1:
            audit.error(label + ".split", split, "[0,1]", row)
            return
        r = rates(inputs, split)
        for k, v in r.items():
            if (k in result or k in {"rw", "rs", "sum_rate"}) and result.get(k) is None:
                audit.error(label + "." + k + ".mask", result.get(k), "accepted rate", row)
            elif k in result:
                if k.startswith("gamma_"):
                    audit.sinr(label + "." + k, result[k], v, row, rate_tolerance)
                else:
                    audit.close(
                        label + "." + k,
                        result[k],
                        v,
                        objective_tolerance if k == "sum_rate" else rate_tolerance,
                        row,
                    )
        for k, v in oma(inputs).items():
            if k in result:
                audit.close(label + "." + k, result[k], v, rate_tolerance, row)
        if min(r["rw"] - inputs[3], r["rs"] - inputs[4]) < -rate_tolerance:
            audit.error(label + ".original_constraints", split, "QoS witness", row)
        audit.eq(label + ".candidate_a.identity", candidate, split, row)
        audit.eq(
            label + ".optimality_status.acceptance",
            result.get("optimality_status") in {"numerical-concavity-bound", "exact-singleton"},
            True,
            row,
        )
        gap = result.get("objective_gap_bound")
        if gap is None or not math.isfinite(gap) or not 0 <= gap <= objective_tolerance:
            audit.error(
                label + ".objective_gap_bound.acceptance",
                gap,
                "[0, declared objective tolerance]",
                row,
            )


def replay_job(checks, raw_rows, params, solve, audit, budget_check=None):
    n = params["oracle_rows"]
    tighter = params["sensitivity_rows"]
    ids = [c["row"] for c in checks]
    audit.eq("oracle.coverage", ids, list(range(n)))
    if len(raw_rows) < n:
        raise ValueError("missing raw replay row")
    base_count = tight_count = 0
    statuses = {}
    status_counts = {"base": {}, "tighter": {}}
    unresolved = dict.fromkeys(("analytic", "independent", "base", "tighter"), 0)
    not_established = dict.fromkeys(("independent", "base", "tighter"), 0)
    not_applicable = dict.fromkeys(("independent", "base", "tighter"), 0)
    classification_transitions, optimality_transitions = {}, {}
    pairs = (
        "analytic_base",
        "analytic_tighter",
        "base_tighter",
        "analytic_independent",
        "base_independent",
        "tighter_independent",
    )
    comparisons = {
        pair: dict(
            resolved_classifications=0,
            classification_conflicts=0,
            accepted_objectives=0,
            objective_failures=0,
            objective_max_residual=None,
            unresolved=0,
            optimality_not_established=0,
        )
        for pair in pairs
    }

    def compare(pair, left, right, row):
        count = comparisons[pair]
        label = "oracle.agreement." + pair
        if "unresolved" in (left["status"], right["status"]):
            count["unresolved"] += 1
        else:
            count["resolved_classifications"] += 1
            count["classification_conflicts"] += int(left["status"] != right["status"])
            audit.eq(label + ".status", left["status"], right["status"], row)
        if any(x["status"] != "infeasible" and not x["established"] for x in (left, right)):
            count["optimality_not_established"] += 1
        if (
            left["status"] == right["status"] == "feasible"
            and left["established"]
            and right["established"]
        ):
            a, b = left["objective"], right["objective"]
            if a is None or b is None or not math.isfinite(a) or not math.isfinite(b):
                audit.error(label + ".objective", (a, b), "finite accepted objectives", row)
                count["objective_failures"] += 1
                return
            residual = abs(a - b)
            count["accepted_objectives"] += 1
            count["objective_max_residual"] = max(count["objective_max_residual"] or 0, residual)
            count["objective_failures"] += int(residual > OBJECTIVE)
            audit.close(label + ".objective", a, b, OBJECTIVE, row)

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
        independent = noma_adjudicate(inputs)
        independent_objective = None
        if independent["status"] == "feasible" and independent.get("high") is not None:
            try:
                independent_objective = rates(inputs, independent["high"])["sum_rate"]
            except ValueError:
                # Unsupported binary64 domains cannot establish an independent optimum.
                independent_objective = None
        independent_established = independent_objective is not None
        if independent["status"] == "unresolved" or (
            independent["status"] == "feasible" and not independent_established
        ):
            audit.ambiguities.append(
                dict(
                    row=row,
                    method="independent-oracle-comparison",
                    independent_status=independent["status"],
                    reason=independent.get("certificate"),
                    optimality_status="not-established",
                )
            )
        unresolved["analytic"] += int(raw["status"] == "unresolved")
        unresolved["independent"] += int(independent["status"] == "unresolved")
        not_established["independent"] += int(
            independent["status"] == "unresolved"
            or (independent["status"] == "feasible" and not independent_established)
        )
        not_applicable["independent"] += int(independent["status"] == "infeasible")
        evidence = dict(
            analytic=dict(
                status=raw["status"], objective=expected, established=raw["status"] == "feasible"
            ),
            independent=dict(
                status=independent["status"],
                objective=independent_objective,
                established=independent_established,
            ),
        )
        compare("analytic_independent", evidence["analytic"], evidence["independent"], row)
        replayed = {}
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
            if budget_check is not None:
                budget_check()
            regenerated = solve(*inputs, **kwargs)
            if budget_check is not None:
                budget_check()
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
            check_oracle_original(audit, key, c[key], inputs, row, kwargs)
            normalized = {
                k: None if isinstance(v, float) and math.isnan(v) else v
                for k, v in regenerated.items()
            }
            check_oracle_original(audit, key + ".regenerated", normalized, inputs, row, kwargs)
            for k, v in kwargs.items():
                audit.eq(key + "." + k, c[key].get(k), v, row)
            statuses[regenerated["status"]] = statuses.get(regenerated["status"], 0) + 1
            kind = "base" if factor == 1 else "tighter"
            status = regenerated["status"]
            status_counts[kind][status] = status_counts[kind].get(status, 0) + 1
            unresolved[kind] += int(status == "unresolved")
            established = regenerated.get("optimality_status") in {
                "numerical-concavity-bound",
                "exact-singleton",
            }
            not_established[kind] += int(status != "infeasible" and not established)
            not_applicable[kind] += int(status == "infeasible")
            evidence[kind] = dict(
                status=status, objective=regenerated.get("sum_rate"), established=established
            )
            replayed[kind] = regenerated
            compare("analytic_" + kind, evidence["analytic"], evidence[kind], row)
            compare(kind + "_independent", evidence[kind], evidence["independent"], row)
            if factor == 1:
                base_count += 1
            else:
                tight_count += 1
        if "base" in evidence and "tighter" in evidence:
            compare("base_tighter", evidence["base"], evidence["tighter"], row)
            transition = evidence["base"]["status"] + "->" + evidence["tighter"]["status"]
            classification_transitions[transition] = (
                classification_transitions.get(transition, 0) + 1
            )
            transition = (
                replayed["base"]["optimality_status"]
                + "->"
                + replayed["tighter"]["optimality_status"]
            )
            optimality_transitions[transition] = optimality_transitions.get(transition, 0) + 1
    audit.eq("oracle.base_count", base_count, n)
    audit.eq("oracle.tight_count", tight_count, tighter)
    return dict(
        base=base_count,
        tighter=tight_count,
        statuses=statuses,
        base_statuses=status_counts["base"],
        tighter_statuses=status_counts["tighter"],
        comparisons=comparisons,
        unresolved_counts=unresolved,
        optimality_not_established_counts=not_established,
        optimality_not_applicable_counts=not_applicable,
        classification_transitions=classification_transitions,
        optimality_transitions=optimality_transitions,
        evidence_kind="shared-pinned-oracle-reproduction-with-independent-original-constraint-comparisons",
    )
