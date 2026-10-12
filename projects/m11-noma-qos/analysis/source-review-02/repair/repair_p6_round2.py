from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py');s=p.read_text()
s=s.replace('def require_ready_source_review(project):','def require_ready_source_review(project, budget_check=None):')
s=s.replace('    for name, digest in ready["source_hashes"].items():\n        file', '    for name, digest in ready["source_hashes"].items():\n        if budget_check:\n            budget_check()\n        file')
s=s.replace('            raise ValueError("Source changed after enforced review: " + name)\n    return ready','            raise ValueError("Source changed after enforced review: " + name)\n        if budget_check:\n            budget_check()\n    return ready')
a=s.index('def run_native(');b=s.index('\ndef combined_assessment',a)
s=s[:a]+'''def manifest_path_inventory(project):
    return sorted(f.relative_to(project).as_posix() for f in (project / "results/runs").glob("*/manifest.json"))


def write_completion_receipt(directory, project, report_name):
    save(directory / "completion-receipt.json", dict(
        finished=now(), report=report_name,
        evidence_hashes={f.relative_to(project).as_posix(): sha256(f) for f in sorted(directory.rglob("*")) if f.is_file() and f.name != "completion-receipt.json"},
        status=load(directory / report_name)["status"], scientific_gate_approval=False))


def run_native(project):
    """Invoke the unmodified native API and retain its acceptance separately."""
    from lab.verification import verify

    directory = new_run_directory("native")
    report = dict(status="INCOMPLETE", started=now(), run_directory=str(directory),
                  native_acceptance_status="NOT_INVOKED", native_api_invoked=False,
                  canonical_scientific_subprocess_executed=None)
    started = time.monotonic()
    reviewed = None
    try:
        reviewed = require_ready_source_review(project)["source_hashes"]
        report["reviewed_source_hashes"] = reviewed
        report["native_api_invoked"] = True
        report["native_acceptance_status"] = "REJECTED_OR_INCOMPLETE"
        report["native_report"] = verify(project)
        report["status"] = report["native_report"]["status"]
        report["native_acceptance_status"] = report["status"]
        report["canonical_scientific_subprocess_executed"] = report["native_report"].get("mode") == "model-specific independent verifier"
    except subprocess.TimeoutExpired as exc:
        report.update(exception="TimeoutExpired: " + str(exc), timeout_seconds=exc.timeout, failure_kind="timeout")
        for name, body in (("stdout.txt", exc.stdout), ("stderr.txt", exc.stderr)):
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body or ""
            (directory / name).write_text(text, encoding="utf-8", newline="\\n")
    except Exception as exc:
        report.update(exception=type(exc).__name__ + ": " + str(exc), failure_kind="execution-or-integrity-incomplete")
        checks_path = project / "analysis/verifier-output/checks.yaml"
        if checks_path.is_file():
            checks = load(checks_path)
            report["native_checks"] = checks
            failed_checks = [key for key, value in checks.items() if value.get("passed") is False]
            if failed_checks == ["statistical-precision"]:
                report.update(status="INCONCLUSIVE", failure_kind="statistical-precision")
            elif failed_checks:
                report.update(status="FAIL", failure_kind="numerical-contradiction", failed_native_checks=failed_checks)
    finally:
        try:
            report["reviewed_source_bindings_rechecked"] = require_ready_source_review(project)["source_hashes"] == reviewed if reviewed is not None else None
            if report["reviewed_source_bindings_rechecked"] is False:
                report.update(status="INCOMPLETE", failure_kind="source-integrity")
            report["native_output_hashes"] = {
                f.relative_to(project).as_posix(): sha256(f)
                for f in [project / "analysis/verification.json", project / "analysis/verification.yaml", *sorted((project / "analysis/verifier-output").rglob("*"))]
                if f.is_file()
            }
        except Exception as exc:
            report.update(status="INCOMPLETE", failure_kind="source-or-output-integrity", binding_error=str(exc))
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
        if any(j.get("replay", {}).get(key) != planned[key] for key in ("base", "tighter")) or j.get("rows") != planned["rows"]:
            return False
    scenarios = supplement.get("scenarios", {})
    if set(scenarios) != set(expected_scenarios):
        return False
    category_keys = {"n00", "n01", "n10", "n11", "unresolved"}
    moments = {"n", "mean", "variance", "ci95", "halfwidth", "relative_halfwidth", "precision_met"}
    for name, planned in expected_scenarios.items():
        value = scenarios[name]
        if value.get("deterministic") != planned["deterministic"] or value.get("N_total") != planned["rows"]:
            return False
        for field in ("counts", "independent_counts"):
            counts = value.get(field, {})
            if set(counts) != category_keys or any(type(x) is not int or x < 0 for x in counts.values()) or sum(counts.values()) != planned["rows"]:
                return False
        counts = value["counts"]
        if value.get("N_resolved") != planned["rows"] - counts["unresolved"] or value.get("unresolved") != counts["unresolved"]:
            return False
        pairs = value.get("paired", {})
        if set(pairs) != {"sum_rate", "oma_sum", "paired_difference"}:
            return False
        for stat in pairs.values():
            if not moments <= set(stat) or stat["n"] != counts["n11"]:
                return False
            if planned["deterministic"] and (stat["ci95"] is not None or stat["halfwidth"] is not None):
                return False
        events = value.get("events", {})
        if planned["deterministic"]:
            if events:
                return False
        else:
            if set(events) != {"noma_infeasibility", "oma_infeasibility", "oma_only"}:
                return False
            for event in events.values():
                if not {"events", "denominator", "estimate", "ci95", "minimum_events_met", "zero_event_upper_bound"} <= set(event) or event["denominator"] != value["N_resolved"]:
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
    if native.get("reviewed_source_hashes") != ready["source_hashes"] or supplement.get("reviewed_source_hashes") != ready["source_hashes"]:
        raise ValueError("Assessment source bindings differ from reviewed sources")
    spec, _ = locked(project)
    inventory = read_inventory(project)
    check_jobs([m for _, m in inventory], spec)
    expected_jobs = {m["run_id"]: dict(rows=m["params"]["trials"], base=m["params"]["oracle_rows"], tighter=m["params"]["sensitivity_rows"]) for _, m in inventory}
    expected_scenarios = {v["id"]: dict(rows=v["trials"]*len(v["seeds"]), deterministic=v["params"]["kind"] == "deterministic") for v in spec["scenarios"]}
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
        for name, digest in {**report.get("input_hashes", {}), **native.get("native_output_hashes", {})}.items():
            file = project.parents[1] / name.removeprefix("@repo/") if name.startswith("@repo/") else within(project, name)
            if sha256(file) != digest:
                raise ValueError("Native evidence changed: " + name)
        items = load(project / "analysis/verification.yaml")
        for item in items:
            VerificationItem.model_validate(item)
    return native, supplement, items, dict(status="PASS", expected_jobs=expected_jobs, expected_scenarios=expected_scenarios)

''' + s[b:]
s=s.replace('def combined_assessment(native, supplement, native_items, evidence_paths):','def combined_assessment(native, supplement, native_items, evidence_paths, validation=None):')
s=s.replace('    failed = native.get("status") != "PASS" or supplement.get("status") == "FAIL" or errors > 0','    failed = native.get("failure_kind") == "numerical-contradiction" or supplement.get("status") == "FAIL" or errors > 0')
a=s.index('    coverage = (',s.index('def combined_assessment'));b=s.index('    failed |=',a)
s=s[:a]+'''    coverage = bool(validation and validation.get("status") == "PASS") and assessment_coverage(supplement, validation["expected_jobs"], validation["expected_scenarios"]) and supplement.get("status") == "CHECKS_COMPLETE" and all(supplement.get(k) is True for k in ("bindings_rechecked", "source_bindings_rechecked", "inventory_paths_rechecked"))
''' + s[b:]
s=s.replace('    for scenario, value in supplement.get("scenarios", {}).items():\n        for field', '    for scenario, value in supplement.get("scenarios", {}).items():\n        if value.get("deterministic") is True:\n            continue\n        for field')
s=s.replace('or any(i["verdict"] != "PASS" for i in native_items)','or any(i["verdict"] == "FAIL" for i in native_items)')
s=s.replace('        not coverage\n', '        native.get("status") != "PASS"\n        or not coverage\n')
s=s.replace('        or len(native_items) != 7\n', '        or len(native_items) != 7\n        or any(i["verdict"] != "PASS" for i in native_items)\n')
s=s.replace('else "approximation-gap"\n                if inconclusive','else "statistical-noise"\n                if precision or native.get("failure_kind") == "statistical-precision"\n                else "approximation-gap"\n                if inconclusive')
s=s.replace('native_acceptance_status=native.get("status"),','native_acceptance_status=native.get("native_acceptance_status", native.get("status")),\n        selected_native_invocation_status=native.get("status"),\n        native_failure_kind=native.get("failure_kind"),')
# Full reviewed dependency/inventory binding and final budget accounting.
s=s.replace('    bindings = {}\n    traced =', '    bindings = {}\n    budget = None\n    reviewed = None\n    inventory_paths = None\n    traced =')
s=s.replace('        require_ready_source_review(project)\n        budget.check()\n        paths', '        reviewed = require_ready_source_review(project, budget.check)["source_hashes"]\n        receipt["reviewed_source_hashes"] = reviewed\n        inventory_paths = manifest_path_inventory(project)\n        receipt["manifest_path_inventory"] = inventory_paths\n        budget.check()\n        paths')
s=s.replace('            receipt["source_bindings_rechecked"] = source_snapshot() == sources','''            if budget:
                budget.check()
            current_reviewed = require_ready_source_review(project, budget.check if budget else None)["source_hashes"] if reviewed is not None else None
            receipt["source_bindings_rechecked"] = source_snapshot() == sources and current_reviewed == reviewed
            receipt["inventory_paths_rechecked"] = manifest_path_inventory(project) == inventory_paths if inventory_paths is not None else None
            if receipt["inventory_paths_rechecked"] is False:
                raise ValueError("Lineage manifest inventory changed")''')
s=s.replace('receipt["bindings_rechecked"] = (\n                all(sha256(within(project, name)) == digest for name, digest in bindings.items())\n                if bindings\n                else None\n            )','''receipt["bindings_rechecked"] = None
            if bindings:
                receipt["bindings_rechecked"] = True
                for name, digest in bindings.items():
                    if budget:
                        budget.check()
                    if sha256(within(project, name)) != digest:
                        receipt["bindings_rechecked"] = False
            if budget:
                budget.check()''')
s=s.replace('        except Exception as exc:\n            receipt.update(status="FAIL", binding_error=str(exc))','        except (TimeoutError, MemoryError) as exc:\n            receipt.update(status="INCOMPLETE", binding_error=str(exc))\n        except Exception as exc:\n            receipt.update(status="FAIL", binding_error=str(exc))')
s=s.replace('        receipt.update(\n            finished=now(),','        receipt.update(\n            finished=now(),')
s=s.replace('        save(directory / "lineage-receipt.json", receipt)','        save(directory / "lineage-receipt.json", receipt)\n        write_completion_receipt(directory, project, "lineage-receipt.json")')
s=s.replace('    snapshots = None\n    items = []','    snapshots = None\n    budget = None\n    reviewed = None\n    inventory_paths = None\n    items = []')
s=s.replace('        require_ready_source_review(project)\n        budget.check()\n        spec, lock', '        reviewed = require_ready_source_review(project, budget.check)["source_hashes"]\n        report["reviewed_source_hashes"] = reviewed\n        budget.check()\n        spec, lock')
s=s.replace('        items = read_inventory(project)\n        check_jobs', '        items = read_inventory(project)\n        inventory_paths = manifest_path_inventory(project)\n        report["manifest_path_inventory"] = inventory_paths\n        check_jobs')
s=s.replace('            runtime_s=time.monotonic() - started,\n            peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1],\n            finished=now(),','')
a=s.index('        try:\n            report["source_bindings_rechecked"] =',s.index('def execute(project'));b=s.index('        save(directory / "execution-report.json", report)',a)
s=s[:a]+'''        try:
            if budget:
                budget.check()
            current_reviewed = require_ready_source_review(project, budget.check if budget else None)["source_hashes"] if reviewed is not None else None
            report["source_bindings_rechecked"] = source_snapshot() == sources and current_reviewed == reviewed
            report["inventory_paths_rechecked"] = manifest_path_inventory(project) == inventory_paths if inventory_paths is not None else None
            if report["inventory_paths_rechecked"] is False:
                raise ValueError("Manifest inventory changed during execution")
            report["bindings_rechecked"] = input_snapshot(project, read_inventory(project), budget.check if budget else None) == snapshots if snapshots is not None else None
            if budget:
                budget.check()
            if report["source_bindings_rechecked"] is False or report["bindings_rechecked"] is False:
                report["status"] = "FAIL"
        except (TimeoutError, MemoryError) as binding_error:
            report.update(status="INCOMPLETE", binding_error=str(binding_error))
        except Exception as binding_error:
            report.update(status="FAIL", bindings_rechecked=False, binding_error=str(binding_error))
        report.update(runtime_s=time.monotonic() - started, finished=now(), peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1])
''' + s[b:]
s=s.replace('        save(directory / "execution-report.json", report)','        save(directory / "execution-report.json", report)\n        write_completion_receipt(directory, project, "execution-report.json")')
# Write standalone recipes, executable without extraction.
s=s.replace('            records.append(\n                dict(','''            recipe_path = directory / "lineage-recipes" / (scenario + "-" + column + ".json")
            save(recipe_path, recipe)
            records.append(
                dict(
                    recipe_path=recipe_path.relative_to(project).as_posix(),''')
s=s.replace('    parser.add_argument("--assess", type=str)','    parser.add_argument("--assess", type=str)\n    parser.add_argument("--native-receipt", type=str)')
a=s.index('    elif args.assess:');b=s.index('    elif args.lineage_recipe:',a)
s=s[:a]+'''    elif args.assess:
        if not args.native_receipt:
            parser.error("--assess requires the explicit --native-receipt of the attempt being assessed")
        directory = new_run_directory("assessment")
        try:
            supplemental = within(project, args.assess)
            native_path = within(project, args.native_receipt)
            native, supplement, items, validation = validate_assessment_inputs(project, native_path, supplemental)
            value = combined_assessment(native, supplement, items, [native_path.relative_to(project).as_posix(), supplemental.relative_to(project).as_posix()], validation)
            value["selected_evidence_hashes"] = {f.relative_to(project).as_posix(): sha256(f) for f in (native_path, supplemental)}
        except Exception as exc:
            value = dict(status="INCOMPLETE", eligible_for_gate_request=False, full_scientific_validation=False, exception=type(exc).__name__ + ": " + str(exc))
        save(directory / "combined-assessment.json", value)
        if "verification_items" in value:
            save(directory / "combined-verification.yaml", value["verification_items"])
        write_completion_receipt(directory, project, "combined-assessment.json")
        print(str(directory))
        print(value["status"])
        if value["status"] != "PASS":
            raise SystemExit(2)
''' +s[b:]
p.write_text(s,encoding='utf-8',newline='\n')
