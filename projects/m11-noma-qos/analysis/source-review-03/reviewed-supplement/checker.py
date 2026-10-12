"""Prepared P6 supplemental checker. Production execution requires --execute."""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import time
import tracemalloc
import uuid
from itertools import zip_longest
from pathlib import Path

from independent import (
    CHANNEL_COLUMNS,
    METRIC_COLUMNS,
    OBJECTIVE,
    RATE,
    SPLIT,
    Audit,
    Moments,
    binomial,
    check_jobs,
    check_row,
    rates,
    reference,
    seeded,
)
from replay import load_shared, replay_job

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))


def native_utilities():
    from lab.io import load, now, save, sha256, within
    from lab.simulation import locked, manifest_output, verify_manifest
    from lab.state import ensure_phase

    return load, now, save, sha256, within, locked, manifest_output, verify_manifest, ensure_phase


load, now, save, sha256, within, locked, manifest_output, verify_manifest, ensure_phase = (
    native_utilities()
)


def source_snapshot():
    return {p.name: sha256(p) for p in sorted(HERE.glob("*.py"))}


def input_snapshot(project, manifests, budget_check=None):
    names = [
        "model/model-spec.tex",
        "model/assumptions.yaml",
        "model/notation.yaml",
        "model/predictions.yaml",
        "sim/protocol.yaml",
        "sim/protocol.md",
        "sim/cases.yaml",
        "sim/lock.json",
        "research-state.yaml",
        "results/statistics.json",
    ]
    result = {}
    for n in names:
        if budget_check:
            budget_check()
        result[n] = sha256(within(project, n))
        if budget_check:
            budget_check()
    for p, m in manifests:
        result[p.relative_to(project).as_posix()] = sha256(p)
        for o in m["outputs"]:
            if budget_check:
                budget_check()
            # All scientific files are project-local in the approved manifests.
            if o.get("storage", "project") != "project":
                raise ValueError("unexpected external result storage")
            file = within(project, o["path"])
            digest = sha256(file)
            if digest != o["sha256"] or file.stat().st_size != o["bytes"]:
                raise ValueError("input output binding mismatch")
            result[o["path"]] = digest
            if budget_check:
                budget_check()
    return result


def read_inventory(project):
    paths = sorted((project / "results/runs").glob("*/manifest.json"))
    return [(p, load(p)) for p in paths]


# P6 review fixes: statistical roundoff, cooperative budgets, scoped reports and lineage.
# Probability comparison is dimensionless numerical interoperability, not a solver tolerance.
PROBABILITY_ROUNDOFF = 64 * math.ulp(1.0)


def compare_probability(audit, label, actual, expected):
    if expected is None:
        audit.eq(label, actual, None)
        return
    try:
        value = float(actual)
    except (TypeError, ValueError):
        audit.error(label, actual, "finite probability")
        return
    if not math.isfinite(value) or not 0 <= value <= 1:
        audit.error(label, actual, "probability in [0,1]")
        return
    audit.close(label, value, expected, PROBABILITY_ROUNDOFF)


class Budget:
    """Cooperative checkpoints; Python traced allocations, not an OS memory bound."""

    def __init__(self, args):
        for key in ("max_job_seconds", "max_total_seconds", "max_memory_mb"):
            value = getattr(args, key)
            if isinstance(value, bool) or not math.isfinite(float(value)) or value <= 0:
                raise ValueError(key + " must be finite and positive")
        self.args = args
        self.started = time.monotonic()

    def check(self, job_started=None):
        current = time.monotonic()
        if current - self.started > self.args.max_total_seconds:
            raise TimeoutError("total deadline exceeded; incomplete")
        if job_started is not None and current - job_started > self.args.max_job_seconds:
            raise TimeoutError("job deadline exceeded; incomplete")
        if (
            tracemalloc.is_tracing()
            and tracemalloc.get_traced_memory()[1] > self.args.max_memory_mb * 1024 * 1024
        ):
            raise MemoryError("Python traced allocation threshold exceeded; incomplete")


def new_run_directory(kind):
    directory = HERE / "runs" / (now().replace(":", "-") + "-" + uuid.uuid4().hex + "-" + kind)
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def require_ready_source_review(project, budget_check=None):
    ready = load(project / "analysis/source-review-ready.json")
    if ready.get("recommendation") != "ready" or not ready.get("enforced_independent_review"):
        raise ValueError("Enforced independent source review is not ready")
    if not isinstance(ready.get("source_hashes"), dict) or len(ready["source_hashes"]) != 19:
        raise ValueError("Source review must bind the full approved 19-source inventory")
    expected = load(project / "analysis/P6-code-review-payload.json")["artifact_paths"]
    if set(ready["source_hashes"]) != set(expected):
        raise ValueError("Source review inventory differs from approved packet")
    root = project.parents[1]
    for name, digest in ready["source_hashes"].items():
        if budget_check:
            budget_check()
        file = root / name.removeprefix("@repo/") if name.startswith("@repo/") else project / name
        if sha256(file) != digest:
            raise ValueError("Source changed after enforced review: " + name)
        if budget_check:
            budget_check()
    return ready


def manifest_path_inventory(project):
    return sorted(
        f.relative_to(project).as_posix()
        for f in (project / "results/runs").glob("*/manifest.json")
    )


def write_completion_receipt(directory, project, report_name):
    save(
        directory / "completion-receipt.json",
        dict(
            finished=now(),
            report=report_name,
            evidence_hashes={
                f.relative_to(project).as_posix(): sha256(f)
                for f in sorted(directory.rglob("*"))
                if f.is_file() and f.name != "completion-receipt.json"
            },
            status=load(directory / report_name)["status"],
            scientific_gate_approval=False,
        ),
    )


def run_native(project):
    """Invoke the unmodified native API and retain its acceptance separately."""
    from lab.verification import verify

    directory = new_run_directory("native")
    report = dict(
        status="INCOMPLETE",
        started=now(),
        run_directory=str(directory),
        native_acceptance_status="NOT_INVOKED",
        native_api_invoked=False,
        canonical_scientific_subprocess_executed=None,
    )
    started = time.monotonic()
    reviewed = None
    stage_existed_before = (project / "analysis/verifier-output").exists()
    report["stage_existed_before"] = stage_existed_before
    try:
        reviewed = require_ready_source_review(project)["source_hashes"]
        report["reviewed_source_hashes"] = reviewed
        report["native_api_invoked"] = True
        report["native_acceptance_status"] = "REJECTED_OR_INCOMPLETE"
        report["native_report"] = verify(project)
        report["status"] = report["native_report"]["status"]
        report["native_acceptance_status"] = report["status"]
        report["canonical_scientific_subprocess_executed"] = (
            report["native_report"].get("mode") == "model-specific independent verifier"
        )
    except subprocess.TimeoutExpired as exc:
        report.update(
            exception="TimeoutExpired: " + str(exc),
            timeout_seconds=exc.timeout,
            failure_kind="timeout",
        )
        for name, body in (("stdout.txt", exc.stdout), ("stderr.txt", exc.stderr)):
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body or ""
            (directory / name).write_text(text, encoding="utf-8", newline="\n")
    except Exception as exc:
        report.update(
            exception=type(exc).__name__ + ": " + str(exc),
            failure_kind="execution-or-integrity-incomplete",
        )
        checks_path = project / "analysis/verifier-output/checks.yaml"
        if not stage_existed_before and checks_path.is_file():
            checks = load(checks_path)
            report["native_checks"] = checks
            failed_checks = [key for key, value in checks.items() if value.get("passed") is False]
            if failed_checks == ["statistical-precision"]:
                report.update(status="INCONCLUSIVE", failure_kind="statistical-precision")
            elif failed_checks:
                report.update(
                    status="FAIL",
                    failure_kind="numerical-contradiction",
                    failed_native_checks=failed_checks,
                )
    finally:
        try:
            report["reviewed_source_bindings_rechecked"] = (
                require_ready_source_review(project)["source_hashes"] == reviewed
                if reviewed is not None
                else None
            )
            if report["reviewed_source_bindings_rechecked"] is False:
                report.update(status="INCOMPLETE", failure_kind="source-integrity")
            report["native_output_hashes"] = {
                f.relative_to(project).as_posix(): sha256(f)
                for f in [
                    project / "analysis/verification.json",
                    project / "analysis/verification.yaml",
                    *sorted((project / "analysis/verifier-output").rglob("*")),
                ]
                if f.is_file()
            }
        except Exception as exc:
            report.update(
                status="INCOMPLETE",
                failure_kind="source-or-output-integrity",
                binding_error=str(exc),
            )
        report.update(finished=now(), runtime_s=time.monotonic() - started)
        save(directory / "native-receipt.json", report)
        write_completion_receipt(directory, project, "native-receipt.json")
    return report


def assessment_coverage(supplement, expected_jobs, expected_scenarios):
    """Exact planned identities, per-job budgets and all required summary fields."""
    if not expected_jobs or not expected_scenarios:
        return False
    jobs = supplement.get("jobs", [])
    if len(jobs) != len(expected_jobs) or len({j.get("run_id") for j in jobs}) != len(jobs):
        return False
    if {j.get("run_id") for j in jobs} != set(expected_jobs):
        return False
    for j in jobs:
        planned = expected_jobs[j["run_id"]]
        if (
            any(j.get("replay", {}).get(key) != planned[key] for key in ("base", "tighter"))
            or j.get("rows") != planned["rows"]
        ):
            return False
    scenarios = supplement.get("scenarios", {})
    if set(scenarios) != set(expected_scenarios):
        return False
    category_keys = {"n00", "n01", "n10", "n11", "unresolved"}
    moments = {"n", "mean", "variance", "ci95", "halfwidth", "relative_halfwidth", "precision_met"}
    for name, planned in expected_scenarios.items():
        value = scenarios[name]
        if (
            value.get("deterministic") != planned["deterministic"]
            or value.get("N_total") != planned["rows"]
        ):
            return False
        for field in ("counts", "independent_counts"):
            counts = value.get(field, {})
            if (
                set(counts) != category_keys
                or any(type(x) is not int or x < 0 for x in counts.values())
                or sum(counts.values()) != planned["rows"]
            ):
                return False
        counts = value["counts"]
        if (
            value.get("N_resolved") != planned["rows"] - counts["unresolved"]
            or value.get("unresolved") != counts["unresolved"]
        ):
            return False
        pairs = value.get("paired", {})
        if set(pairs) != {"sum_rate", "oma_sum", "paired_difference"}:
            return False
        for stat in pairs.values():
            if not moments <= set(stat) or stat["n"] != counts["n11"]:
                return False
            if planned["deterministic"] and (
                stat["ci95"] is not None or stat["halfwidth"] is not None
            ):
                return False
        events = value.get("events", {})
        if planned["deterministic"]:
            if events:
                return False
        else:
            if set(events) != {"noma_infeasibility", "oma_infeasibility", "oma_only"}:
                return False
            for event in events.values():
                if (
                    not {
                        "events",
                        "denominator",
                        "estimate",
                        "ci95",
                        "minimum_events_met",
                        "zero_event_upper_bound",
                    }
                    <= set(event)
                    or event["denominator"] != value["N_resolved"]
                ):
                    return False
        if set(value.get("ablations", {})) != {"fixed", "grid"}:
            return False
    return True


def validate_assessment_inputs(project, native_path, supplement_path):
    """Select a native attempt explicitly; stale files never substitute for it."""
    from lab.models import VerificationItem

    ready = require_ready_source_review(project)
    native = load(native_path)
    supplement = load(supplement_path)
    for path in (native_path, supplement_path):
        completion = load(path.parent / "completion-receipt.json")
        if completion["report"] != path.name or completion["status"] != load(path)["status"]:
            raise ValueError("Completion receipt identity/status mismatch")
        hashes = completion["evidence_hashes"]
        if path.relative_to(project).as_posix() not in hashes:
            raise ValueError("Selected report missing from completion bindings")
        for name, digest in hashes.items():
            if sha256(within(project, name)) != digest:
                raise ValueError("Completion evidence changed: " + name)
    if (
        native.get("reviewed_source_hashes") != ready["source_hashes"]
        or supplement.get("reviewed_source_hashes") != ready["source_hashes"]
    ):
        raise ValueError("Assessment source bindings differ from reviewed sources")
    spec, _ = locked(project)
    inventory = read_inventory(project)
    check_jobs([m for _, m in inventory], spec)
    expected_jobs = {
        m["run_id"]: dict(
            rows=m["params"]["trials"],
            base=m["params"]["oracle_rows"],
            tighter=m["params"]["sensitivity_rows"],
        )
        for _, m in inventory
    }
    expected_scenarios = {
        v["id"]: dict(
            rows=v["trials"] * len(v["seeds"]), deterministic=v["params"]["kind"] == "deterministic"
        )
        for v in spec["scenarios"]
    }
    if not assessment_coverage(supplement, expected_jobs, expected_scenarios):
        raise ValueError("Assessment lacks exact planned coverage/statistical fields")
    if supplement.get("manifest_path_inventory") != manifest_path_inventory(project):
        raise ValueError("Assessment manifest-path inventory changed")
    if input_snapshot(project, inventory) != supplement.get("input_hashes"):
        raise ValueError("Supplement input bindings changed")
    items = []
    if native.get("status") == "PASS" and native.get("native_acceptance_status") == "PASS":
        report = native.get("native_report", {})
        if report != load(project / "analysis/verification.json"):
            raise ValueError("Selected native attempt differs from current native report")
        for name, digest in {
            **report.get("input_hashes", {}),
            **native.get("native_output_hashes", {}),
        }.items():
            file = (
                project.parents[1] / name.removeprefix("@repo/")
                if name.startswith("@repo/")
                else within(project, name)
            )
            if sha256(file) != digest:
                raise ValueError("Native evidence changed: " + name)
        items = load(project / "analysis/verification.yaml")
        for item in items:
            VerificationItem.model_validate(item)
    return (
        native,
        supplement,
        items,
        dict(status="PASS", expected_jobs=expected_jobs, expected_scenarios=expected_scenarios),
    )


def combined_assessment(native, supplement, native_items, evidence_paths, validation=None):
    """Scientific assessment supplements the immutable legacy acceptance route."""
    errors = sum(supplement.get("error_counts", {}).values())
    failed = (
        native.get("failure_kind") == "numerical-contradiction"
        or supplement.get("status") == "FAIL"
        or errors > 0
    )
    coverage = (
        bool(validation and validation.get("status") == "PASS")
        and assessment_coverage(
            supplement, validation["expected_jobs"], validation["expected_scenarios"]
        )
        and supplement.get("status") == "CHECKS_COMPLETE"
        and all(
            supplement.get(k) is True
            for k in (
                "bindings_rechecked",
                "source_bindings_rechecked",
                "inventory_paths_rechecked",
            )
        )
    )
    failed |= any(
        supplement.get(k) is False for k in ("bindings_rechecked", "source_bindings_rechecked")
    )
    oracle_uncertainty = sum(supplement.get("oracle_unresolved_counts", {}).values()) + sum(
        supplement.get("oracle_optimality_not_established_counts", {}).values()
    )
    unresolved = supplement.get("stored_unresolved_rows", 0) + supplement.get(
        "unsupported_resolved_predicates", 0
    )
    precision = []
    for scenario, value in supplement.get("scenarios", {}).items():
        if value.get("deterministic") is True:
            continue
        for field, statistic in value.get("paired", {}).items():
            if (
                statistic.get("n", 0) > 0
                and statistic.get("ci95") is not None
                and not statistic.get("precision_met")
            ):
                precision.append(scenario + "." + field)
            elif statistic.get("precision_met") is False and statistic.get("n", 0) > 0:
                precision.append(scenario + "." + field)
        for field, event in value.get("events", {}).items():
            if event.get("events", 0) > 0 and not event.get("minimum_events_met"):
                precision.append(scenario + ".events." + field)
    native_by_id = {i["prediction_ref"]: i for i in native_items}
    if native_items and (
        set(native_by_id) != set("P" + str(i) for i in range(1, 8))
        or any(i["verdict"] == "FAIL" for i in native_items)
    ):
        failed = True
    inconclusive = (
        native.get("status") != "PASS"
        or not coverage
        or unresolved > 0
        or oracle_uncertainty > 0
        or bool(precision)
        or len(native_items) != 7
        or any(i["verdict"] != "PASS" for i in native_items)
    )
    verdict = "FAIL" if failed else "INCONCLUSIVE" if inconclusive else "PASS"
    items = []
    for i in range(1, 8):
        items.append(
            dict(
                id="supplement-P" + str(i),
                prediction_ref="P" + str(i),
                method="Combined native receipts and independently recomputed planned finite-input checks; unresolved/unsupported coverage is retained",
                metric="source-reviewed finite coverage and original-constraint consistency",
                value=None,
                tolerance=dict(
                    rate=RATE,
                    split=SPLIT,
                    objective=OBJECTIVE,
                    scope="approved planned numerical regimes; not universal validation",
                    unresolved=unresolved,
                ),
                verdict=verdict,
                triage="implementation-bug"
                if failed
                else "statistical-noise"
                if precision or native.get("failure_kind") == "statistical-precision"
                else "approximation-gap"
                if inconclusive
                else None,
                evidence_paths=evidence_paths,
            )
        )
    return dict(
        status=verdict,
        eligible_for_gate_request=verdict == "PASS",
        verification_items=items,
        native_acceptance_status=native.get("native_acceptance_status", native.get("status")),
        selected_native_invocation_status=native.get("status"),
        native_failure_kind=native.get("failure_kind"),
        supplement_status=supplement.get("status"),
        stored_and_unsupported_unresolved=unresolved,
        oracle_uncertainty=oracle_uncertainty,
        failed_precision=precision,
        full_scientific_validation=False,
        limitations=[
            "Legacy native PASS is retained as its own receipt.",
            "Combined assessment does not rewrite native or locked science.",
            "Retained uncertainty is never promoted to scientific PASS.",
            "Finite planned checks do not prove arbitrary real-input validity.",
        ],
    )


def lineage_value(rows, recipe, budget_check=None):
    """Executable independent conditional mean recipe, excluding undecided blocks explicitly."""
    from independent import finite_inputs, noma_adjudicate, oma, oma_adjudicate

    if (
        recipe.get("op") != "independent_conditional_mean"
        or recipe.get("mask") != "independent_both_feasible"
        or recipe.get("column") not in {"sum_rate", "oma_sum", "paired_difference"}
    ):
        raise ValueError("Unsupported executable lineage operation/mask/column")
    moment = Moments()
    count = unresolved = 0
    for raw in rows:
        count += 1
        if budget_check and count % 128 == 1:
            budget_check()
        inputs = finite_inputs([float(raw[k]) for k in ("P", "gw", "gs", "qw", "qs")])
        ns = noma_adjudicate(inputs)
        os = oma_adjudicate(inputs)
        if "unresolved" in (ns["status"], os):
            unresolved += 1
            continue
        if ns["status"] != "feasible" or os != "feasible":
            continue
        if raw["status"] != "feasible":
            raise ValueError("Lineage raw classification contradicts original constraints")
        split = float(raw["a_star"])
        if not math.isfinite(split) or not 0 <= split <= 1:
            raise ValueError("Undefined accepted lineage split")
        if ns.get("high") is None or abs(split - ns["high"]) > SPLIT:
            raise ValueError("Lineage selected endpoint does not match independent U")
        nr = rates(inputs, split)
        if abs(nr["rw_site"] - (inputs[3] if inputs[0] > 0 and inputs[1] > 0 else 0.0)) > RATE:
            raise ValueError("Lineage selected endpoint weak target is not active")
        od = oma(inputs)
        if nr["rw"] < inputs[3] - RATE or nr["rs"] < inputs[4] - RATE:
            raise ValueError("Lineage accepted split violates original constraints")
        values = {
            "sum_rate": nr["sum_rate"],
            "oma_sum": od["oma_sum"],
            "paired_difference": nr["sum_rate"] - od["oma_sum"],
        }
        moment.add(values[recipe["column"]])
    return dict(
        value=moment.mean if moment.n else None,
        n=moment.n,
        rows=count,
        independently_unresolved_rows=unresolved,
        statistics=moment.summary(),
        status="INCONCLUSIVE" if unresolved or not moment.n else "COMPUTED",
    )


def execute_lineage_recipe(project, recipe, args=None):
    directory = new_run_directory("lineage")
    started = time.monotonic()
    sources = source_snapshot()
    receipt = dict(
        status="INCOMPLETE",
        started=now(),
        run_directory=str(directory),
        recipe=recipe,
        source_hashes=sources,
        canonical_execution=False,
        memory_scope="Python traced allocations after initialization; excludes native/OS memory",
        time_scope="cooperative checkpoints; individual native calls may overshoot",
    )
    bindings = {}
    budget = None
    reviewed = None
    inventory_paths = None
    traced = tracemalloc.is_tracing()
    if not traced:
        tracemalloc.start()
    try:
        args = args or argparse.Namespace(
            max_job_seconds=3600, max_total_seconds=86400, max_memory_mb=1024
        )
        budget = Budget(args)
        budget.check()
        reviewed = require_ready_source_review(project, budget.check)["source_hashes"]
        receipt["reviewed_source_hashes"] = reviewed
        inventory_paths = manifest_path_inventory(project)
        receipt["manifest_path_inventory"] = inventory_paths
        budget.check()
        paths = recipe.get("source_manifests", [])
        if not paths or len(set(paths)) != len(paths):
            raise ValueError("Nonempty unique lineage source manifest list required")
        raw_files = []
        for name in paths:
            job_started = time.monotonic()
            budget.check(job_started)
            file = within(project, name)
            m = verify_manifest(project, load(file))
            budget.check(job_started)
            if m is None:
                from lab.models import RunManifest

                m = RunManifest.model_validate(load(file))
            raw = manifest_output(project, m, "channels.csv")
            bindings[name] = sha256(file)
            budget.check(job_started)
            bindings[raw.relative_to(project).as_posix()] = sha256(raw)
            budget.check(job_started)
            raw_files.append(raw)
        if bindings != recipe["input_hashes"]:
            raise ValueError("Lineage recipe input binding mismatch")

        def rows():
            for file in raw_files:
                job_started = time.monotonic()
                with file.open(encoding="utf-8", newline="") as stream:
                    for index, row in enumerate(csv.DictReader(stream)):
                        if index % 128 == 0:
                            budget.check(job_started)
                        yield row
                budget.check(job_started)

        result = lineage_value(rows(), recipe, budget.check)
        budget.check()
        if result["rows"] != recipe["rows"]:
            raise ValueError("Lineage planned row coverage mismatch")
        receipt.update(result, input_hashes=bindings)
    except Exception as exc:
        receipt["exception"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        try:
            if budget:
                budget.check()
            current_reviewed = (
                require_ready_source_review(project, budget.check if budget else None)[
                    "source_hashes"
                ]
                if reviewed is not None
                else None
            )
            receipt["source_bindings_rechecked"] = (
                source_snapshot() == sources and current_reviewed == reviewed
            )
            receipt["inventory_paths_rechecked"] = (
                manifest_path_inventory(project) == inventory_paths
                if inventory_paths is not None
                else None
            )
            if receipt["inventory_paths_rechecked"] is False:
                raise ValueError("Lineage manifest inventory changed")
            receipt["bindings_rechecked"] = None
            if bindings:
                receipt["bindings_rechecked"] = True
                for name, digest in bindings.items():
                    if budget:
                        budget.check()
                    if sha256(within(project, name)) != digest:
                        receipt["bindings_rechecked"] = False
            if budget:
                budget.check()
            if (
                receipt["source_bindings_rechecked"] is False
                or receipt["bindings_rechecked"] is False
            ):
                receipt["status"] = "FAIL"
                receipt["binding_error"] = "Source/input changed during lineage execution"
        except (TimeoutError, MemoryError) as exc:
            receipt.update(status="INCOMPLETE", binding_error=str(exc))
        except Exception as exc:
            receipt.update(status="FAIL", binding_error=str(exc))
        receipt.update(
            finished=now(),
            runtime_s=time.monotonic() - started,
            peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1],
        )
        save(directory / "lineage-receipt.json", receipt)
        write_completion_receipt(directory, project, "lineage-receipt.json")
        if not traced:
            tracemalloc.stop()
    return receipt


def write_lineage(project, items, summaries, directory, audit, budget_check=None):
    """Record executable recipes corresponding to actual independent streaming moments."""
    records = []
    for scenario, summary in summaries.items():
        if budget_check:
            budget_check()
        selected = [(file, m) for file, m in items if m["scenario"] == scenario]
        hashes = {}
        paths = []
        for file, m in selected:
            name = file.relative_to(project).as_posix()
            paths.append(name)
            hashes[name] = sha256(file)
            raw = next(o for o in m["outputs"] if Path(o["path"]).name == "channels.csv")
            hashes[raw["path"]] = raw["sha256"]
        for column, moment in summary["independent_pairs"].items():
            recipe = dict(
                op="independent_conditional_mean",
                column=column,
                mask="independent_both_feasible",
                source_manifests=paths,
                input_hashes=hashes,
                rows=summary["total"],
            )
            recipe_path = directory / "lineage-recipes" / (scenario + "-" + column + ".json")
            save(recipe_path, recipe)
            records.append(
                dict(
                    recipe_path=recipe_path.relative_to(project).as_posix(),
                    key=scenario + "-" + column,
                    unit="bit/s/Hz",
                    recipe=recipe,
                    value=moment.mean if moment.n else None,
                    n=moment.n,
                    independent_counts=summary["independent_counts"],
                    status="UNVERIFIED_DUE_TO_ERRORS"
                    if not audit.ok()
                    else "INCONCLUSIVE"
                    if summary["independent_counts"]["unresolved"] or not moment.n
                    else "COMPUTED",
                    statistics=moment.summary(),
                    used_in=[
                        "P6 scenario-level analysis; native manuscript claims use only its supported operations"
                    ],
                )
            )
    save(
        directory / "claim-lineage.json",
        dict(
            records=records,
            source_hashes=source_snapshot(),
            executable_command="python analysis/supplement/checker.py --lineage-recipe <project-relative-json-recipe>",
            denominator="independently resolved both-feasible blocks",
            undefined_denominator="null value, no substituted zero",
        ),
    )


def init_scenario():
    return dict(
        counts={k: 0 for k in ("n00", "n01", "n10", "n11", "unresolved")},
        total=0,
        independent_counts={k: 0 for k in ("n00", "n01", "n10", "n11", "unresolved")},
        pairs={k: Moments() for k in ("sum_rate", "oma_sum", "paired_difference")},
        independent_pairs={k: Moments() for k in ("sum_rate", "oma_sum", "paired_difference")},
        reference={k: Moments() for k in ("oma_rw", "oma_rs", "oma_sum")},
        loss={k: Moments() for k in ("fixed", "grid")},
        min_loss={"fixed": None, "grid": None},
        found={"fixed": 0, "grid": 0},
        negative=0,
        violations=0,
        runtime=0.0,
    )


def update(s, raw, checked):
    inputs, ns, os, cat, paired, od, ab = checked
    s["counts"][cat] += 1
    s["total"] += 1
    from independent import category

    s["independent_counts"][category(ns["status"], os)] += 1
    for k, v in od.items():
        if k in s["reference"]:
            s["reference"][k].add(v)
    if cat == "n11":
        values = dict(
            sum_rate=rates(inputs, float(raw["a_star"]))["sum_rate"],
            oma_sum=od["oma_sum"],
            paired_difference=paired,
        )
        for k, v in values.items():
            s["pairs"][k].add(v)
        if ns["status"] == "feasible" and os == "feasible":
            for k, v in values.items():
                s["independent_pairs"][k].add(v)
        s["negative"] += int(paired < -RATE)
    s["violations"] += int(raw["candidate_violation"] == "True")
    for kind in ("fixed", "grid"):
        found = ab["fixed_feasible" if kind == "fixed" else "grid_found_feasible"] == 1
        s["found"][kind] += int(found)
        if found and raw["status"] == "feasible":
            loss = rates(inputs, float(raw["a_star"]))["sum_rate"] - ab[kind + "_sum"]
            s["loss"][kind].add(loss)
            s["min_loss"][kind] = (
                loss if s["min_loss"][kind] is None else min(s["min_loss"][kind], loss)
            )


def compare_nullable(audit, label, actual, expected, tol=RATE):
    if expected is None:
        audit.eq(label, actual, None)
    elif actual is None:
        audit.error(label, actual, expected)
    else:
        audit.close(label, actual, expected, tol)


def compare_moments(audit, label, stored, moment, deterministic=False):
    summary = moment.summary(deterministic)
    if deterministic:
        audit.eq(label, stored, None)
        return summary
    if moment.n == 0:
        audit.eq(label, stored, None)
        return summary
    if not isinstance(stored, dict):
        audit.error(label, stored, "statistic object")
        return summary
    audit.eq(label + ".n", stored.get("n"), moment.n)
    for k in ("mean", "halfwidth"):
        compare_nullable(audit, label + "." + k, stored.get(k), summary[k])
    relative = stored.get("relative_halfwidth")
    reconstructed = (
        stored.get("halfwidth") / abs(stored["mean"])
        if stored.get("halfwidth") is not None and stored.get("mean")
        else None
    )
    compare_nullable(audit, label + ".relative_halfwidth.consistency", relative, reconstructed, 0.0)
    if relative is not None and summary["relative_halfwidth"] is not None:
        audit.diagnostic(label + ".relative_halfwidth", relative, summary["relative_halfwidth"])
    if relative is not None and summary["halfwidth"] is not None:
        audit.close(
            label + ".relative_halfwidth.implied_halfwidth",
            relative * abs(summary["mean"]),
            summary["halfwidth"],
            RATE,
        )
    ci = summary["ci95"]
    for k, i in (("low", 0), ("high", 1)):
        compare_nullable(audit, label + "." + k, stored.get(k), ci[i] if ci else None)
    return summary


def compare_scenario(audit, stored, s, scenario):
    deterministic = scenario["params"]["kind"] == "deterministic"
    counts = s["counts"]
    total = s["total"]
    resolved = total - counts["unresolved"]
    for k, v in counts.items():
        audit.eq("statistics.counts." + k, stored["counts"].get(k), v)
    for k, v in (
        ("N_total", total),
        ("N_resolved", resolved),
        ("paired_denominator", counts["n11"]),
        ("negative_paired_count", s["negative"]),
        ("candidate_violation_count", s["violations"]),
        ("params", scenario["params"]),
        ("deterministic_replicates_not_independent", deterministic),
    ):
        audit.eq("statistics." + k, stored.get(k), v)
    pairs = {}
    for k, m in s["pairs"].items():
        audit.eq("independent.paired_denominator." + k, m.n, counts["n11"])
        pairs[k] = compare_moments(
            audit, "statistics.paired." + k, stored["paired_statistics"].get(k), m, deterministic
        )
        if not deterministic:
            audit.eq(
                "statistics.precision." + k,
                stored["rate_precision"].get(k),
                pairs[k]["precision_met"],
            )
    events = {}
    if not deterministic:
        for k, event in (
            ("noma_infeasibility", counts["n00"] + counts["n01"]),
            ("oma_infeasibility", counts["n00"] + counts["n10"]),
            ("oma_only", counts["n01"]),
        ):
            b = binomial(event, resolved)
            events[k] = b
            old = stored["event_statistics"][k]
            for field, value in (
                ("events", event),
                ("trials", resolved),
                ("conclusive", b["minimum_events_met"]),
            ):
                audit.eq("statistics.events." + k + "." + field, old.get(field), value)
            for field, value in (
                ("estimate", b["estimate"]),
                ("low", b["ci95"][0] if b["ci95"] else None),
                ("high", b["ci95"][1] if b["ci95"] else None),
                ("zero_event_upper_bound", b["zero_event_upper_bound"]),
            ):
                if field == "estimate":
                    compare_nullable(
                        audit, "statistics.events." + k + "." + field, old.get(field), value, 0.0
                    )
                else:
                    compare_probability(
                        audit, "statistics.events." + k + "." + field, old.get(field), value
                    )
    else:
        audit.eq("statistics.deterministic.events", stored["event_statistics"], {})
        audit.eq("statistics.deterministic.precision", stored["rate_precision"], {})
    for method in ("noma", "oma"):
        n = counts["n11"] + counts["n10" if method == "noma" else "n01"]
        compare_nullable(
            audit,
            "statistics." + method + "_feasibility_fraction",
            stored[method + "_feasibility_fraction"],
            n / resolved if resolved else None,
            0.0,
        )
    absum = {}
    for kind, m in s["loss"].items():
        old = stored["ablations"][kind]
        for k, v in (("paired_n", m.n), ("found_feasible_count", s["found"][kind])):
            audit.eq("statistics.ablation." + kind + "." + k, old.get(k), v)
        for k, v in (("mean_loss", m.mean if m.n else None), ("minimum_loss", s["min_loss"][kind])):
            compare_nullable(
                audit, "statistics.ablation." + kind + "." + k, old.get(k), v, OBJECTIVE
            )
        if s["min_loss"][kind] is not None and s["min_loss"][kind] < -OBJECTIVE:
            audit.error(
                "statistics.ablation." + kind + ".negative_loss",
                s["min_loss"][kind],
                ">=-objective_tolerance",
            )
        absum[kind] = dict(
            n=m.n,
            mean_loss=m.mean if m.n else None,
            minimum_loss=s["min_loss"][kind],
            found=s["found"][kind],
        )
    return dict(
        counts=counts,
        deterministic=deterministic,
        independent_counts=s["independent_counts"],
        N_total=total,
        N_resolved=resolved,
        unresolved=counts["unresolved"],
        paired=pairs,
        events=events,
        ablations=absum,
    )


def compare_reference(audit, old, scenarios, spec):
    expected = [
        s for s in spec["scenarios"] if s["params"].get("qw") == 0 and s["params"].get("qs") == 0
    ]
    points = old["points"]
    audit.eq("reference.coverage", [p["scenario"] for p in points], [s["id"] for s in expected])
    previous = None
    summary = []
    for scenario, p in zip(expected, points):
        params = scenario["params"]
        P = params["P"]
        ref = reference(P)
        s = scenarios[scenario["id"]]
        audit.eq("reference.P_db", p["P_db"], params["P_db"])
        actual = {}
        for k, r in (("oma_rw", ref["weak"]), ("oma_rs", ref["strong"])):
            audit.close("reference.equation." + k, p["reference"][k], r, RATE)
            actual[k] = compare_moments(
                audit, "reference.actual." + k, p["actual"][k], s["reference"][k]
            )
            relative = abs(s["reference"][k].mean - r) / r
            audit.diagnostic("reference.relative." + k, p["relative_error"][k], relative)
            audit.close(
                "reference.relative.implied_absolute_error." + k,
                p["relative_error"][k] * r,
                abs(s["reference"][k].mean - r),
                RATE,
            )
            if relative > 0.05:
                audit.error("reference.5percent." + k, relative, "<=.05")
        audit.eq(
            "reference.point.agreement",
            p["agreement"],
            all(
                abs(s["reference"][k].mean - p["reference"][k]) / p["reference"][k] <= 0.05
                for k in ("oma_rw", "oma_rs")
            ),
        )
        weak, strong = s["reference"]["oma_rw"].mean, s["reference"]["oma_rs"].mean
        if not strong > weak:
            audit.error("reference.order", strong, f">{weak}")
        if previous and not (weak > previous[0] and strong > previous[1]):
            audit.error("reference.trend", (weak, strong), previous)
        previous = (weak, strong)
        summary.append(dict(scenario=scenario["id"], references=ref, actual=actual))
    for k in ("ordering", "trend", "agreement"):
        audit.eq("reference." + k, old[k], True)
    return summary


def process_job(
    project, manifest, case_table, s, audit, solve, max_seconds, ambiguity_stream, budget_check=None
):
    start = time.monotonic()
    initial_error_count = sum(audit.counts.values())

    def check_budget():
        if time.monotonic() - start > max_seconds:
            raise TimeoutError("per-job deadline exceeded; incomplete")
        if budget_check:
            budget_check(start)

    check_budget()
    params = manifest.params
    seed = manifest.seeds[0]
    deterministic = params["kind"] == "deterministic"
    n = params["trials"]
    channel_path = manifest_output(project, manifest, "channels.csv")
    metric_path = manifest_output(project, manifest, "metrics.csv")
    sampling = load(manifest_output(project, manifest, "sampling.json"))
    expected_sampling = dict(
        kind=params["kind"],
        seed=seed,
        trials=n,
        bit_generator="PCG64",
        seed_sequence_entropy=[seed, 0],
        stream="none; fixed cases" if deterministic else "channel",
        channel_law="fixed case table" if deterministic else "sorted iid exponential mean 1",
        common_grid_draws=True,
        deterministic_repeats_independent=False,
        no_noise_or_initialization_stream_required=True,
    )
    audit.eq("sampling.schema", sampling, expected_sampling)
    gains = None if deterministic else seeded(seed, n)
    replay_rows = []
    ambiguity_count = 0
    unsupported_resolved_predicates = 0
    independent_counts = {k: 0 for k in ("n00", "n01", "n10", "n11", "unresolved")}
    ledger = {k: 0 for k in ("n00", "n01", "n10", "n11", "unresolved")}
    rows = 0
    with (
        channel_path.open(encoding="utf8", newline="") as cf,
        metric_path.open(encoding="utf8", newline="") as mf,
    ):
        cr, mr = csv.DictReader(cf), csv.DictReader(mf)
        columns = (
            CHANNEL_COLUMNS if deterministic else [k for k in CHANNEL_COLUMNS if k != "case_id"]
        )
        audit.eq("channels.schema", cr.fieldnames, columns)
        audit.eq("metrics.schema", mr.fieldnames, METRIC_COLUMNS)
        for row, (raw, metric) in enumerate(zip_longest(cr, mr)):
            if raw is None or metric is None:
                raise ValueError("CSV alignment length mismatch")
            if row >= n:
                raise ValueError("extra row")
            if None in raw or None in metric:
                raise ValueError("malformed CSV row width")
            if deterministic:
                case = case_table[row % len(case_table)]
                inputs = list(map(float, case["values"]))
                case_id = case["id"]
            else:
                inputs = [params["P"], *map(float, gains[row]), params["qw"], params["qs"]]
                case_id = ""
            before = len(audit.ambiguities)
            checked = check_row(raw, metric, inputs, case_id, row, audit)
            ambiguity_count += len(audit.ambiguities[before:])
            from independent import category

            independent_counts[category(checked[1]["status"], checked[2])] += 1
            for amb in audit.ambiguities[before:]:
                unsupported_resolved_predicates += int(amb["stored_status"] != "unresolved")
                amb.update(
                    run_id=manifest.run_id,
                    unsupported_resolved_predicate=amb["stored_status"] != "unresolved",
                )
                ambiguity_stream.write(json.dumps(amb, allow_nan=False) + "\n")
            # Keep bounded ambiguity details in memory; count separately in file.
            del audit.ambiguities[before:]
            update(s, raw, checked)
            ledger[checked[3]] += 1
            if row < params["oracle_rows"]:
                replay_rows.append(raw)
            rows += 1
            if row % 128 == 0:
                check_budget()
    audit.eq("rows.coverage", rows, n)
    if rows == 0:
        raise ValueError("empty job")
    expected_ledger = {**ledger, "N_total": rows, "N_resolved": rows - ledger["unresolved"]}
    audit.eq("ledger", load(manifest_output(project, manifest, "ledger.json")), expected_ledger)
    oracle = load(manifest_output(project, manifest, "oracle.json"))
    audit.eq("oracle.schema", set(oracle), {"checks"})
    before_replay = len(audit.ambiguities)
    replay = replay_job(
        oracle["checks"], replay_rows, params, solve, audit, budget_check=check_budget
    )
    for ambiguity in audit.ambiguities[before_replay:]:
        ambiguity.update(run_id=manifest.run_id, evidence_kind="shared-oracle-comparison")
        ambiguity_stream.write(json.dumps(ambiguity, allow_nan=False) + "\n")
        ambiguity_count += 1
    del audit.ambiguities[before_replay:]
    check_budget()
    s["runtime"] += manifest.runtime_s
    return dict(
        run_id=manifest.run_id,
        rows=rows,
        replay=replay,
        runtime_s=time.monotonic() - start,
        row_error_count=sum(audit.counts.values()) - initial_error_count,
        cumulative_error_count=sum(audit.counts.values()),
        independent_counts=independent_counts,
        ambiguity_entries=ambiguity_count,
        unsupported_resolved_predicates=unsupported_resolved_predicates,
    )


def execute(project, args):
    directory = new_run_directory("supplement")
    started = time.monotonic()
    snapshots = None
    budget = None
    reviewed = None
    inventory_paths = None
    items = []
    sources = source_snapshot()
    audit = Audit()
    records = []
    report = dict(
        status="INCOMPLETE",
        full_scientific_validation=False,
        started=now(),
        run_directory=str(directory),
        source_hashes=sources,
        input_hashes=None,
        jobs=records,
        limits={
            k: str(getattr(args, k))
            for k in ["max_job_seconds", "max_total_seconds", "max_memory_mb"]
        },
        memory_scope="Python allocations traced after initialization; excludes prior imports/native allocations/OS resident memory",
        time_scope="cooperative checkpoints; a native guard/hash/solver call can overshoot until its next checkpoint",
    )
    already_traced = tracemalloc.is_tracing()
    if not already_traced:
        tracemalloc.start()
    try:
        budget = Budget(args)
        budget.check()
        ensure_phase(project, "P6")
        budget.check()
        reviewed = require_ready_source_review(project, budget.check)["source_hashes"]
        report["reviewed_source_hashes"] = reviewed
        budget.check()
        spec, lock = locked(project)
        budget.check()
        items = read_inventory(project)
        inventory_paths = manifest_path_inventory(project)
        report["manifest_path_inventory"] = inventory_paths
        check_jobs([m for _, m in items], spec)
        budget.check()
        snapshots = input_snapshot(project, items, budget.check)
        report["input_hashes"] = snapshots
        summaries = {s["id"]: init_scenario() for s in spec["scenarios"]}
        cases = load(project / "sim/cases.yaml")["cases"]
        if len(cases) != 20:
            raise ValueError("deterministic table coverage")
        solve = load_shared(project / "sim/src/oracle.py")
        with (
            (directory / "ambiguities.jsonl").open("w", encoding="utf-8", newline="\n") as amb,
            (directory / "execution.jsonl").open("w", encoding="utf-8", newline="\n") as log,
        ):
            for _, raw_manifest in items:
                budget.check()
                manifest = verify_manifest(
                    project, raw_manifest
                )  # unmodified native production guard, once/job
                budget.check()
                if manifest is None:
                    from lab.models import RunManifest

                    manifest = RunManifest.model_validate(raw_manifest)
                record = process_job(
                    project,
                    manifest,
                    cases,
                    summaries[manifest.scenario],
                    audit,
                    solve,
                    args.max_job_seconds,
                    amb,
                    budget_check=budget.check,
                )
                records.append(record)
                log.write(json.dumps(record, allow_nan=False) + "\n")
                log.flush()
                print(json.dumps(record), flush=True)
                budget.check()
        old = load(project / "results/statistics.json")
        budget.check()
        expected_hashes = {file.relative_to(project).as_posix(): sha256(file) for file, _ in items}
        audit.eq("statistics.manifest_bindings", old["input_manifest_hashes"], expected_hashes)
        audit.eq(
            "statistics.scenario_coverage",
            [s["scenario"] for s in old["scenarios"]],
            sorted(summaries),
        )
        report["scenarios"] = {}
        by_id = {s["scenario"]: s for s in old["scenarios"]}
        for scenario in spec["scenarios"]:
            budget.check()
            report["scenarios"][scenario["id"]] = compare_scenario(
                audit, by_id[scenario["id"]], summaries[scenario["id"]], scenario
            )
        report["oma_reference"] = compare_reference(
            audit, old["baseline_reproduction"], summaries, spec
        )
        base_statuses = {"feasible": 0, "infeasible": 0, "unresolved": 0}
        maxima = []
        for record in records:
            for key, value in record["replay"]["base_statuses"].items():
                base_statuses[key] += value
            maximum = record["replay"]["comparisons"]["analytic_base"]["objective_max_residual"]
            if maximum is not None:
                maxima.append(maximum)
        audit.eq("statistics.oracle_status_counts", old["oracle_status_counts"], base_statuses)
        audit.close(
            "statistics.maximum_oracle_sum_difference",
            old["maximum_oracle_sum_difference"],
            max(maxima, default=0.0),
            OBJECTIVE,
        )
        report["oracle_base_statuses"] = base_statuses
        report["maximum_analytic_base_objective_difference"] = max(maxima, default=None)
        audit.eq("full.jobs", len(records), 145)
        audit.eq(
            "full.rows",
            sum(r["rows"] for r in records),
            sum(s["trials"] * len(s["seeds"]) for s in spec["scenarios"]),
        )
        audit.eq("full.oracle", sum(r["replay"]["base"] for r in records), 4708)
        audit.eq("full.tighter", sum(r["replay"]["tighter"] for r in records), 1160)
        budget.check()
        report["oracle_unresolved_counts"] = {
            kind: sum(r["replay"]["unresolved_counts"][kind] for r in records)
            for kind in ("analytic", "independent", "base", "tighter")
        }
        report["oracle_optimality_not_applicable_counts"] = {
            kind: sum(r["replay"]["optimality_not_applicable_counts"][kind] for r in records)
            for kind in ("independent", "base", "tighter")
        }
        report["oracle_optimality_not_established_counts"] = {
            kind: sum(r["replay"]["optimality_not_established_counts"][kind] for r in records)
            for kind in ("independent", "base", "tighter")
        }
        write_lineage(project, items, summaries, directory, audit, budget.check)
        budget.check()
        unsupported = sum(r["unsupported_resolved_predicates"] for r in records)
        declared = sum(s["counts"]["unresolved"] for s in summaries.values())
        ambiguous = (
            (directory / "ambiguities.jsonl").stat().st_size > 0
            or declared > 0
            or any(report["oracle_unresolved_counts"].values())
            or any(report["oracle_optimality_not_established_counts"].values())
        )
        report.update(unsupported_resolved_predicates=unsupported, stored_unresolved_rows=declared)
        report["status"] = (
            "FAIL"
            if not audit.ok()
            else "INCOMPLETE"
            if unsupported
            else "CHECKED_WITH_DECLARED_UNRESOLVED"
            if ambiguous
            else "CHECKS_COMPLETE"
        )
        report["supplemental_checks_complete"] = report["status"] == "CHECKS_COMPLETE"
    except Exception as exc:
        report["exception"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        report.update(
            error_counts=audit.counts,
            errors=audit.errors,
            dimensionless_diagnostic_counts=audit.diagnostic_counts,
            dimensionless_diagnostics=audit.diagnostics,
        )
        try:
            if budget:
                budget.check()
            current_reviewed = (
                require_ready_source_review(project, budget.check if budget else None)[
                    "source_hashes"
                ]
                if reviewed is not None
                else None
            )
            report["source_bindings_rechecked"] = (
                source_snapshot() == sources and current_reviewed == reviewed
            )
            report["inventory_paths_rechecked"] = (
                manifest_path_inventory(project) == inventory_paths
                if inventory_paths is not None
                else None
            )
            if report["inventory_paths_rechecked"] is False:
                raise ValueError("Manifest inventory changed during execution")
            report["bindings_rechecked"] = (
                input_snapshot(project, read_inventory(project), budget.check if budget else None)
                == snapshots
                if snapshots is not None
                else None
            )
            if budget:
                budget.check()
            if (
                report["source_bindings_rechecked"] is False
                or report["bindings_rechecked"] is False
            ):
                report["status"] = "FAIL"
        except (TimeoutError, MemoryError) as binding_error:
            report.update(status="INCOMPLETE", binding_error=str(binding_error))
        except Exception as binding_error:
            report.update(status="FAIL", bindings_rechecked=False, binding_error=str(binding_error))
        report.update(
            runtime_s=time.monotonic() - started,
            finished=now(),
            peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1],
        )
        save(directory / "execution-report.json", report)
        write_completion_receipt(directory, project, "execution-report.json")
        if not already_traced:
            tracemalloc.stop()
    return report


def prepare(project):
    items = read_inventory(project)
    spec = load(project / "sim/protocol.yaml")
    check_jobs([m for _, m in items], spec)
    value = dict(
        status="PREPARED_ONLY",
        canonical_execution_performed=False,
        prepared=now(),
        approval_commit="398f26d230b7de0194091a36617e0ca0b157f952",
        approved_phase="P6",
        independence="artifact-only; shared oracle replay separately labelled",
        expected=dict(
            jobs=145,
            rows=sum(s["trials"] * len(s["seeds"]) for s in spec["scenarios"]),
            oracle=4708,
            tighter=1160,
        ),
        sources=source_snapshot(),
        inputs=input_snapshot(project, items),
        tests=load(HERE / "unit-test-results.json"),
        lint=load(HERE / "lint-results.json"),
        synthetic_timing=load(HERE / "synthetic-timing.json"),
        failed_trials=load(HERE / "failed-trials.json"),
        receipt_hashes={
            name: sha256(HERE / name)
            for name in [
                "README.md",
                "unit-test-results.json",
                "unit-tests.log",
                "failed-trials.json",
                "lint-initial.log",
                "lint-results.json",
                "lint-final.log",
                "format-final.log",
                "synthetic-timing.json",
                "synthetic-timing-before-grid-vectorization.json",
            ]
        },
        stored_unresolved_inventory={
            m["run_id"]: load(
                within(
                    project,
                    next(o["path"] for o in m["outputs"] if Path(o["path"]).name == "ledger.json"),
                )
            )["unresolved"]
            for _, m in items
            if load(
                within(
                    project,
                    next(o["path"] for o in m["outputs"] if Path(o["path"]).name == "ledger.json"),
                )
            )["unresolved"]
        },
        limitations=[
            "Canonical execution awaits enforced independent source review.",
            "Monotone noninteger overlapping brackets remain unresolved.",
            "Stored ambiguity and independent ambiguity are preserved separately.",
            "Numerical objective/tie comparisons use declared tolerances; no universal proof.",
        ],
    )
    save(HERE / "preparation.json", value)
    print(json.dumps({k: v for k, v in value.items() if k not in ("sources", "inputs")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--assess", type=str)
    parser.add_argument("--native-receipt", type=str)
    parser.add_argument("--lineage-recipe", type=str)
    parser.add_argument("--max-job-seconds", type=float, default=3600)
    parser.add_argument("--max-total-seconds", type=float, default=86400)
    parser.add_argument("--max-memory-mb", type=int, default=1024)
    args = parser.parse_args()
    project = REPO / "projects/m11-noma-qos"
    if (
        sum(
            bool(v)
            for v in [args.execute, args.prepare, args.native, args.assess, args.lineage_recipe]
        )
        > 1
    ):
        parser.error("choose one operation")
    if args.native:
        report = run_native(project)
        print(json.dumps(report))
        if report["status"] != "PASS":
            raise SystemExit(2)
    elif args.assess:
        if not args.native_receipt:
            parser.error(
                "--assess requires the explicit --native-receipt of the attempt being assessed"
            )
        directory = new_run_directory("assessment")
        try:
            supplemental = within(project, args.assess)
            native_path = within(project, args.native_receipt)
            native, supplement, items, validation = validate_assessment_inputs(
                project, native_path, supplemental
            )
            value = combined_assessment(
                native,
                supplement,
                items,
                [
                    native_path.relative_to(project).as_posix(),
                    supplemental.relative_to(project).as_posix(),
                ],
                validation,
            )
            value["selected_evidence_hashes"] = {
                f.relative_to(project).as_posix(): sha256(f) for f in (native_path, supplemental)
            }
        except Exception as exc:
            value = dict(
                status="INCOMPLETE",
                eligible_for_gate_request=False,
                full_scientific_validation=False,
                exception=type(exc).__name__ + ": " + str(exc),
            )
        save(directory / "combined-assessment.json", value)
        if "verification_items" in value:
            save(directory / "combined-verification.yaml", value["verification_items"])
        write_completion_receipt(directory, project, "combined-assessment.json")
        print(str(directory))
        print(value["status"])
        if value["status"] != "PASS":
            raise SystemExit(2)
    elif args.lineage_recipe:
        recipe = load(within(project, args.lineage_recipe))
        print(json.dumps(execute_lineage_recipe(project, recipe, args)))
    elif args.prepare:
        prepare(project)
    elif args.execute:
        report = execute(project, args)
        print(report["status"])
        if report["status"] != "CHECKS_COMPLETE":
            raise SystemExit(2)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
