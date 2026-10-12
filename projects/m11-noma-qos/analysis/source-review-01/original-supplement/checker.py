"""Prepared P6 supplemental checker. Production execution requires --execute."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import tracemalloc
from itertools import zip_longest
from pathlib import Path

from independent import (
    CHANNEL_COLUMNS,
    METRIC_COLUMNS,
    OBJECTIVE,
    RATE,
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


def input_snapshot(project, manifests):
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
    result = {n: sha256(within(project, n)) for n in names}
    for p, m in manifests:
        result[p.relative_to(project).as_posix()] = sha256(p)
        for o in m["outputs"]:
            # All scientific files are project-local in the approved manifests.
            if o.get("storage", "project") != "project":
                raise ValueError("unexpected external result storage")
            file = within(project, o["path"])
            digest = sha256(file)
            if digest != o["sha256"] or file.stat().st_size != o["bytes"]:
                raise ValueError("input output binding mismatch")
            result[o["path"]] = digest
    return result


def read_inventory(project):
    paths = sorted((project / "results/runs").glob("*/manifest.json"))
    return [(p, load(p)) for p in paths]


def init_scenario():
    return dict(
        counts={k: 0 for k in ("n00", "n01", "n10", "n11", "unresolved")},
        total=0,
        independent_counts={k: 0 for k in ("n00", "n01", "n10", "n11", "unresolved")},
        pairs={k: Moments() for k in ("sum_rate", "oma_sum", "paired_difference")},
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
                compare_nullable(
                    audit, "statistics.events." + k + "." + field, old.get(field), value, 0.0
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
        absum[kind] = dict(
            n=m.n,
            mean_loss=m.mean if m.n else None,
            minimum_loss=s["min_loss"][kind],
            found=s["found"][kind],
        )
    return dict(
        counts=counts,
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


def process_job(project, manifest, case_table, s, audit, solve, max_seconds, ambiguity_stream):
    start = time.monotonic()
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
            if row % 128 == 0 and time.monotonic() - start > max_seconds:
                raise TimeoutError("per-job budget exhausted; incomplete")
    audit.eq("rows.coverage", rows, n)
    if rows == 0:
        raise ValueError("empty job")
    expected_ledger = {**ledger, "N_total": rows, "N_resolved": rows - ledger["unresolved"]}
    audit.eq("ledger", load(manifest_output(project, manifest, "ledger.json")), expected_ledger)
    oracle = load(manifest_output(project, manifest, "oracle.json"))
    audit.eq("oracle.schema", set(oracle), {"checks"})
    replay = replay_job(oracle["checks"], replay_rows, params, solve, audit)
    s["runtime"] += manifest.runtime_s
    return dict(
        run_id=manifest.run_id,
        rows=rows,
        replay=replay,
        runtime_s=time.monotonic() - start,
        row_error_count=sum(audit.counts.values()),
        independent_counts=independent_counts,
        ambiguity_entries=ambiguity_count,
        unsupported_resolved_predicates=unsupported_resolved_predicates,
    )


def execute(project, args):
    ensure_phase(project, "P6")
    spec, lock = locked(project)
    items = read_inventory(project)
    check_jobs([m for _, m in items], spec)
    snapshots = input_snapshot(project, items)
    sources = source_snapshot()
    audit = Audit()
    summaries = {s["id"]: init_scenario() for s in spec["scenarios"]}
    cases = load(project / "sim/cases.yaml")["cases"]
    if len(cases) != 20:
        raise ValueError("deterministic table coverage")
    solve = load_shared(project / "sim/src/oracle.py")
    records = []
    started = time.monotonic()
    tracemalloc.start()
    report = dict(
        status="INCOMPLETE",
        full_scientific_validation=False,
        started=now(),
        input_hashes=snapshots,
        source_hashes=sources,
        jobs=records,
    )
    try:
        with (
            (HERE / "ambiguities.jsonl").open("w", encoding="utf8") as amb,
            (HERE / "execution.jsonl").open("w", encoding="utf8") as log,
        ):
            for _, raw_manifest in items:
                manifest = verify_manifest(project, raw_manifest)  # production guard, once/job
                # Native utility returns validated RunManifest in this repository.
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
                )
                records.append(record)
                log.write(json.dumps(record, allow_nan=False) + "\n")
                log.flush()
                print(json.dumps(record), flush=True)
                if time.monotonic() - started > args.max_total_seconds:
                    raise TimeoutError("total budget exhausted; incomplete")
                if tracemalloc.get_traced_memory()[1] > args.max_memory_mb * 1024 * 1024:
                    raise MemoryError("memory budget exhausted; incomplete")
        old = load(project / "results/statistics.json")
        expected_hashes = {p.relative_to(project).as_posix(): sha256(p) for p, _ in items}
        audit.eq("statistics.manifest_bindings", old["input_manifest_hashes"], expected_hashes)
        audit.eq(
            "statistics.scenario_coverage",
            [s["scenario"] for s in old["scenarios"]],
            sorted(summaries),
        )
        report["scenarios"] = {}
        by_id = {s["scenario"]: s for s in old["scenarios"]}
        for scenario in spec["scenarios"]:
            report["scenarios"][scenario["id"]] = compare_scenario(
                audit, by_id[scenario["id"]], summaries[scenario["id"]], scenario
            )
        report["oma_reference"] = compare_reference(
            audit, old["baseline_reproduction"], summaries, spec
        )
        audit.eq("full.jobs", len(records), 145)
        audit.eq(
            "full.rows",
            sum(r["rows"] for r in records),
            sum(s["trials"] * len(s["seeds"]) for s in spec["scenarios"]),
        )
        audit.eq("full.oracle", sum(r["replay"]["base"] for r in records), 4708)
        audit.eq("full.tighter", sum(r["replay"]["tighter"] for r in records), 1160)
        if input_snapshot(project, items) != snapshots or source_snapshot() != sources:
            raise ValueError("input/source changed during execution")
        # Ambiguous original constraints and unresolved stored ledgers cannot produce a full PASS.
        ambiguous = (HERE / "ambiguities.jsonl").stat().st_size > 0 or any(
            s["counts"]["unresolved"] for s in summaries.values()
        )
        unsupported = sum(r["unsupported_resolved_predicates"] for r in records)
        declared_unresolved = sum(s["counts"]["unresolved"] for s in summaries.values())
        report["unsupported_resolved_predicates"] = unsupported
        report["stored_unresolved_rows"] = declared_unresolved
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
        report["full_scientific_validation"] = False
    except Exception as exc:
        report["exception"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        report.update(
            error_counts=audit.counts,
            errors=audit.errors,
            dimensionless_diagnostic_counts=audit.diagnostic_counts,
            dimensionless_diagnostics=audit.diagnostics,
            runtime_s=time.monotonic() - started,
            peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1],
            finished=now(),
        )
        try:
            report["bindings_rechecked"] = (
                input_snapshot(project, items) == snapshots and source_snapshot() == sources
            )
            if not report["bindings_rechecked"]:
                report["status"] = "FAIL"
        except Exception as binding_error:
            report["bindings_rechecked"] = False
            report["binding_error"] = str(binding_error)
            report["status"] = "FAIL"
        json.dumps(report, allow_nan=False)
        save(HERE / "execution-report.json", report)
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
    parser.add_argument("--max-job-seconds", type=float, default=3600)
    parser.add_argument("--max-total-seconds", type=float, default=86400)
    parser.add_argument("--max-memory-mb", type=int, default=1024)
    args = parser.parse_args()
    project = REPO / "projects/m11-noma-qos"
    if args.execute and args.prepare:
        parser.error("choose prepare or execute")
    if args.prepare:
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
