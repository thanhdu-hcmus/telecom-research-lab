from pathlib import Path
p=Path('projects/m11-noma-qos/analysis/supplement/checker.py')
s=p.read_text(encoding='utf-8')
s=s.replace('import json\n','import json\nimport math\nimport subprocess\nimport uuid\n',1)
extensions=Path('.cache/p6_checker_extensions.py').read_text(encoding='utf-8-sig')
s=s.replace('\ndef init_scenario():','\n'+extensions+'\n\ndef init_scenario():')
s=s.replace('def input_snapshot(project, manifests):','def input_snapshot(project, manifests, budget_check=None):')
s=s.replace('    result = {n: sha256(within(project, n)) for n in names}', '''    result = {}
    for n in names:
        if budget_check: budget_check()
        result[n] = sha256(within(project, n))
        if budget_check: budget_check()''')
s=s.replace('        for o in m["outputs"]:\n','        for o in m["outputs"]:\n            if budget_check: budget_check()\n',1)
s=s.replace('            result[o["path"]] = digest','            result[o["path"]] = digest\n            if budget_check: budget_check()',1)
# Estimates and discrete counts are exact; endpoint numerical roundoff has dimensionless criterion.
s=s.replace('''                compare_nullable(
                    audit, "statistics.events." + k + "." + field, old.get(field), value, 0.0
                )''','''                if field == "estimate":
                    compare_nullable(audit, "statistics.events." + k + "." + field, old.get(field), value, 0.0)
                else:
                    compare_probability(audit, "statistics.events." + k + "." + field, old.get(field), value)''')
# Group-level independently negative ablation losses also fail even with coherent author summaries.
s=s.replace('        absum[kind] = dict(','''        if s["min_loss"][kind] is not None and s["min_loss"][kind] < -OBJECTIVE:
            audit.error("statistics.ablation."+kind+".negative_loss",s["min_loss"][kind],">=-objective_tolerance")
        absum[kind] = dict(''')
# Preserve the old call signature; optional global cooperative budget callback.
s=s.replace('    ambiguity_stream,\n):','    ambiguity_stream,\n    budget_check=None,\n):')
s=s.replace('''    start = time.monotonic()
''','''    start = time.monotonic()
    initial_error_count = sum(audit.counts.values())
    def check_budget():
        if time.monotonic()-start > max_seconds:
            raise TimeoutError("per-job deadline exceeded; incomplete")
        if budget_check: budget_check(start)
    check_budget()
''',1)
s=s.replace('''            if row % 128 == 0 and time.monotonic() - start > max_seconds:
                raise TimeoutError("per-job budget exhausted; incomplete")''','''            if row % 128 == 0:
                check_budget()''')
s=s.replace('    replay = replay_job(oracle["checks"], replay_rows, params, solve, audit)','    replay = replay_job(oracle["checks"], replay_rows, params, solve, audit, budget_check=check_budget)\n    check_budget()')
s=s.replace('row_error_count=sum(audit.counts.values()),','row_error_count=sum(audit.counts.values())-initial_error_count,\n        cumulative_error_count=sum(audit.counts.values()),')
start=s.index('def execute(project, args):');end=s.index('\ndef prepare(project):',start)
new='''def execute(project, args):
    directory = new_run_directory("supplement")
    started=time.monotonic();snapshots=None;items=[];sources=source_snapshot();audit=Audit();records=[]
    report=dict(status="INCOMPLETE",full_scientific_validation=False,started=now(),run_directory=str(directory),
        source_hashes=sources,input_hashes=None,jobs=records,
        limits={k:str(getattr(args,k)) for k in ["max_job_seconds","max_total_seconds","max_memory_mb"]},
        memory_scope="Python allocations traced after initialization; excludes prior imports/native allocations/OS resident memory",
        time_scope="cooperative checkpoints; a native guard/hash/solver call can overshoot until its next checkpoint")
    already_traced=tracemalloc.is_tracing()
    if not already_traced:tracemalloc.start()
    try:
        budget=Budget(args);budget.check()
        ensure_phase(project,"P6");budget.check()
        require_ready_source_review(project);budget.check()
        spec,lock=locked(project);budget.check()
        items=read_inventory(project);check_jobs([m for _,m in items],spec);budget.check()
        snapshots=input_snapshot(project,items,budget.check);report["input_hashes"]=snapshots
        summaries={s["id"]:init_scenario() for s in spec["scenarios"]}
        cases=load(project/"sim/cases.yaml")["cases"]
        if len(cases)!=20:raise ValueError("deterministic table coverage")
        solve=load_shared(project/"sim/src/oracle.py")
        with (directory/"ambiguities.jsonl").open("w",encoding="utf-8",newline="\\n") as amb,(directory/"execution.jsonl").open("w",encoding="utf-8",newline="\\n") as log:
            for _,raw_manifest in items:
                budget.check()
                manifest=verify_manifest(project,raw_manifest) # unmodified native production guard, once/job
                budget.check()
                if manifest is None:
                    from lab.models import RunManifest
                    manifest=RunManifest.model_validate(raw_manifest)
                record=process_job(project,manifest,cases,summaries[manifest.scenario],audit,solve,args.max_job_seconds,amb,budget_check=budget.check)
                records.append(record);log.write(json.dumps(record,allow_nan=False)+"\\n");log.flush()
                print(json.dumps(record),flush=True);budget.check()
        old=load(project/"results/statistics.json");budget.check()
        expected_hashes={file.relative_to(project).as_posix():sha256(file) for file,_ in items}
        audit.eq("statistics.manifest_bindings",old["input_manifest_hashes"],expected_hashes)
        audit.eq("statistics.scenario_coverage",[s["scenario"] for s in old["scenarios"]],sorted(summaries))
        report["scenarios"]={};by_id={s["scenario"]:s for s in old["scenarios"]}
        for scenario in spec["scenarios"]:
            budget.check()
            report["scenarios"][scenario["id"]]=compare_scenario(audit,by_id[scenario["id"]],summaries[scenario["id"]],scenario)
        report["oma_reference"]=compare_reference(audit,old["baseline_reproduction"],summaries,spec)
        base_statuses={"feasible":0,"infeasible":0,"unresolved":0}
        maxima=[]
        for record in records:
            for key,value in record["replay"]["base_statuses"].items():base_statuses[key]+=value
            maximum=record["replay"]["comparisons"]["analytic_base"]["objective_max_residual"]
            if maximum is not None:maxima.append(maximum)
        audit.eq("statistics.oracle_status_counts",old["oracle_status_counts"],base_statuses)
        audit.close("statistics.maximum_oracle_sum_difference",old["maximum_oracle_sum_difference"],max(maxima,default=0.),OBJECTIVE)
        report["oracle_base_statuses"]=base_statuses
        report["maximum_analytic_base_objective_difference"]=max(maxima,default=None)
        audit.eq("full.jobs",len(records),145)
        audit.eq("full.rows",sum(r["rows"] for r in records),sum(s["trials"]*len(s["seeds"]) for s in spec["scenarios"]))
        audit.eq("full.oracle",sum(r["replay"]["base"] for r in records),4708)
        audit.eq("full.tighter",sum(r["replay"]["tighter"] for r in records),1160)
        budget.check();write_lineage(project,items,summaries,directory);budget.check()
        unsupported=sum(r["unsupported_resolved_predicates"] for r in records)
        declared=sum(s["counts"]["unresolved"] for s in summaries.values())
        ambiguous=(directory/"ambiguities.jsonl").stat().st_size>0 or declared>0
        report.update(unsupported_resolved_predicates=unsupported,stored_unresolved_rows=declared)
        report["status"]="FAIL" if not audit.ok() else "INCOMPLETE" if unsupported else "CHECKED_WITH_DECLARED_UNRESOLVED" if ambiguous else "CHECKS_COMPLETE"
        report["supplemental_checks_complete"]=report["status"]=="CHECKS_COMPLETE"
    except Exception as exc:
        report["exception"]=type(exc).__name__+": "+str(exc)
        raise
    finally:
        report.update(error_counts=audit.counts,errors=audit.errors,dimensionless_diagnostic_counts=audit.diagnostic_counts,
            dimensionless_diagnostics=audit.diagnostics,runtime_s=time.monotonic()-started,
            peak_traced_memory_bytes=tracemalloc.get_traced_memory()[1],finished=now())
        try:
            report["source_bindings_rechecked"]=source_snapshot()==sources
            report["bindings_rechecked"]=input_snapshot(project,items)==snapshots if snapshots is not None else None
            if report["source_bindings_rechecked"] is False or report["bindings_rechecked"] is False:report["status"]="FAIL"
        except Exception as binding_error:
            report.update(status="FAIL",bindings_rechecked=False,binding_error=str(binding_error))
        save(directory/"execution-report.json",report)
        if not already_traced:tracemalloc.stop()
    return report

'''
s=s[:start]+new+s[end:]
# Add combined scope, native timeout retention and standalone executable recipes to the existing reviewed CLI source.
s=s.replace('    parser.add_argument("--prepare", action="store_true")','''    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--native",action="store_true")
    parser.add_argument("--assess",type=str)
    parser.add_argument("--lineage-recipe",type=str)''')
s=s.replace('    if args.execute and args.prepare:\n        parser.error("choose prepare or execute")','''    if sum(bool(v) for v in [args.execute,args.prepare,args.native,args.assess,args.lineage_recipe])>1:
        parser.error("choose one operation")''')
s=s.replace('    if args.prepare:\n        prepare(project)','''    if args.native:
        report=run_native(project);print(json.dumps(report))
        if report["status"]!="PASS":raise SystemExit(2)
    elif args.assess:
        native=load(project/"analysis/verification.json")
        items=load(project/"analysis/verification.yaml")
        supplemental=within(project,args.assess)
        value=combined_assessment(native,load(supplemental),items,["analysis/verification.json","analysis/verification.yaml",supplemental.relative_to(project).as_posix()])
        save(project/"analysis/combined-assessment.json",value)
        save(project/"analysis/combined-verification.yaml",value["verification_items"])
        print(value["status"])
        if value["status"]!="PASS":raise SystemExit(2)
    elif args.lineage_recipe:
        recipe=load(within(project,args.lineage_recipe));print(json.dumps(execute_lineage_recipe(project,recipe)))
    elif args.prepare:
        prepare(project)''')
s=s.replace('    inconclusive=not coverage or unresolved>0 or bool(precision)','    inconclusive=not coverage or unresolved>0 or bool(precision) or len(native_items)!=7')
p.write_text(s,encoding='utf-8',newline='\n')
