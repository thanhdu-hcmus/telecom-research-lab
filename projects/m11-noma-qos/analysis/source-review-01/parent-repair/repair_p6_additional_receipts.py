from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py');s=p.read_text()
s=s.replace('    coverage = supplement.get("status") == "CHECKS_COMPLETE"','''    coverage = (
        supplement.get("status") == "CHECKS_COMPLETE"
        and supplement.get("bindings_rechecked") is True
        and supplement.get("source_bindings_rechecked") is True
        and len(supplement.get("jobs", [])) == 145
        and sum(j.get("rows", 0) for j in supplement.get("jobs", [])) == 4718692
        and sum(j.get("replay", {}).get("base", 0) for j in supplement.get("jobs", [])) == 4708
        and sum(j.get("replay", {}).get("tighter", 0) for j in supplement.get("jobs", [])) == 1160
        and bool(supplement.get("scenarios"))
    )
    failed |= any(supplement.get(k) is False for k in ("bindings_rechecked", "source_bindings_rechecked"))
    oracle_uncertainty = sum(supplement.get("oracle_unresolved_counts", {}).values()) + sum(
        supplement.get("oracle_optimality_not_established_counts", {}).values()
    )''')
s=s.replace('    native_by_id = {i["prediction_ref"]: i for i in native_items}','''        for field, event in value.get("events", {}).items():
            if event.get("events", 0) > 0 and not event.get("minimum_events_met"):
                precision.append(scenario + ".events." + field)
    native_by_id = {i["prediction_ref"]: i for i in native_items}''')
s=s.replace('not coverage or unresolved > 0 or bool(precision) or len(native_items) != 7','not coverage or unresolved > 0 or oracle_uncertainty > 0 or bool(precision) or len(native_items) != 7')
s=s.replace('stored_and_unsupported_unresolved=unresolved,','stored_and_unsupported_unresolved=unresolved,\n        oracle_uncertainty=oracle_uncertainty,')
s=s.replace('def lineage_value(rows, recipe):','def lineage_value(rows, recipe, budget_check=None):')
s=s.replace('        count += 1\n        inputs = finite_inputs','        count += 1\n        if budget_check and count % 128 == 1:\n            budget_check()\n        inputs = finite_inputs')
s=s.replace('        nr = rates(inputs, split)\n        od = oma(inputs)','''        if ns.get("high") is None or abs(split - ns["high"]) > SPLIT:
            raise ValueError("Lineage selected endpoint does not match independent U")
        nr = rates(inputs, split)
        if abs(nr["rw_site"] - (inputs[3] if inputs[0] > 0 and inputs[1] > 0 else 0.0)) > RATE:
            raise ValueError("Lineage selected endpoint weak target is not active")
        od = oma(inputs)''')
a=s.index('def execute_lineage_recipe(');b=s.index('\ndef write_lineage',a)
s=s[:a]+'''def execute_lineage_recipe(project, recipe, args=None):
    directory = new_run_directory("lineage")
    sources = source_snapshot()
    receipt = dict(status="INCOMPLETE", started=now(), run_directory=str(directory),
                   recipe=recipe, source_hashes=sources, canonical_execution=False,
                   memory_scope="Python traced allocations after initialization; excludes native/OS memory",
                   time_scope="cooperative checkpoints; individual native calls may overshoot")
    bindings = {}
    traced = tracemalloc.is_tracing()
    if not traced:
        tracemalloc.start()
    try:
        args = args or argparse.Namespace(max_job_seconds=3600, max_total_seconds=86400, max_memory_mb=1024)
        budget = Budget(args)
        budget.check()
        require_ready_source_review(project)
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
            receipt["source_bindings_rechecked"] = source_snapshot() == sources
            receipt["bindings_rechecked"] = all(sha256(within(project, name)) == digest for name, digest in bindings.items()) if bindings else None
            if receipt["source_bindings_rechecked"] is False or receipt["bindings_rechecked"] is False:
                receipt["status"] = "FAIL"
                receipt["binding_error"] = "Source/input changed during lineage execution"
        except Exception as exc:
            receipt.update(status="FAIL", binding_error=str(exc))
        receipt.update(finished=now(), peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1])
        save(directory / "lineage-receipt.json", receipt)
        if not traced:
            tracemalloc.stop()
    return receipt

''' + s[b:]
s=s.replace('def write_lineage(project, items, summaries, directory):','def write_lineage(project, items, summaries, directory, audit, budget_check=None):')
s=s.replace('    for scenario, summary in summaries.items():\n        selected','    for scenario, summary in summaries.items():\n        if budget_check:\n            budget_check()\n        selected')
s=s.replace('        for column, moment in summary["pairs"].items():','        for column, moment in summary["independent_pairs"].items():')
s=s.replace('                    status="INCONCLUSIVE"\n                    if summary','                    status="UNVERIFIED_DUE_TO_ERRORS" if not audit.ok() else "INCONCLUSIVE"\n                    if summary')
s=s.replace('        pairs={k: Moments() for k in ("sum_rate", "oma_sum", "paired_difference")},','        pairs={k: Moments() for k in ("sum_rate", "oma_sum", "paired_difference")},\n        independent_pairs={k: Moments() for k in ("sum_rate", "oma_sum", "paired_difference")},')
s=s.replace('        s["negative"] += int(paired < -RATE)','''        if ns["status"] == "feasible" and os == "feasible":
            for k, v in values.items():
                s["independent_pairs"][k].add(v)
        s["negative"] += int(paired < -RATE)''')
s=s.replace('        counts=counts,\n        independent_counts=', '        counts=counts,\n        deterministic=deterministic,\n        independent_counts=')
s=s.replace('    replay = replay_job(\n', '    before_replay = len(audit.ambiguities)\n    replay = replay_job(\n')
s=s.replace('    check_budget()\n    s["runtime"] +=', '''    for ambiguity in audit.ambiguities[before_replay:]:
        ambiguity.update(run_id=manifest.run_id, evidence_kind="shared-oracle-comparison")
        ambiguity_stream.write(json.dumps(ambiguity, allow_nan=False) + "\\n")
        ambiguity_count += 1
    del audit.ambiguities[before_replay:]
    check_budget()
    s["runtime"] +=''')
s=s.replace('        write_lineage(project, items, summaries, directory)','''        report["oracle_unresolved_counts"] = {
            kind: sum(r["replay"]["unresolved_counts"][kind] for r in records)
            for kind in ("analytic", "independent", "base", "tighter")
        }
        report["oracle_optimality_not_established_counts"] = {
            kind: sum(r["replay"]["optimality_not_established_counts"][kind] for r in records)
            for kind in ("independent", "base", "tighter")
        }
        write_lineage(project, items, summaries, directory, audit, budget.check)''')
s=s.replace('or declared > 0\n        report.update','or declared > 0 or any(report["oracle_unresolved_counts"].values()) or any(report["oracle_optimality_not_established_counts"].values())\n        report.update')
s=s.replace('save(project / "analysis/combined-assessment.json", value)\n        save(project / "analysis/combined-verification.yaml", value["verification_items"])','directory = new_run_directory("assessment")\n        save(directory / "combined-assessment.json", value)\n        save(directory / "combined-verification.yaml", value["verification_items"])\n        print(str(directory))')
s=s.replace('execute_lineage_recipe(project, recipe)))','execute_lineage_recipe(project, recipe, args)))')
p.write_text(s,encoding='utf-8',newline='\n')
