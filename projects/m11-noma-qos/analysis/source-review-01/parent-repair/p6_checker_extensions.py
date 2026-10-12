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
        if current-self.started > self.args.max_total_seconds:
            raise TimeoutError("total deadline exceeded; incomplete")
        if job_started is not None and current-job_started > self.args.max_job_seconds:
            raise TimeoutError("job deadline exceeded; incomplete")
        if tracemalloc.is_tracing() and tracemalloc.get_traced_memory()[1] > self.args.max_memory_mb*1024*1024:
            raise MemoryError("Python traced allocation threshold exceeded; incomplete")


def new_run_directory(kind):
    directory = HERE / "runs" / (now().replace(":", "-") + "-" + uuid.uuid4().hex + "-" + kind)
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def require_ready_source_review(project):
    ready = load(project / "analysis/source-review-ready.json")
    if ready.get("recommendation") != "ready" or not ready.get("enforced_independent_review"):
        raise ValueError("Enforced independent source review is not ready")
    root = project.parents[1]
    for name, digest in ready["source_hashes"].items():
        file = root/name.removeprefix("@repo/") if name.startswith("@repo/") else project/name
        if sha256(file) != digest:
            raise ValueError("Source changed after enforced review: "+name)
    return ready


def run_native(project):
    """Invoke the unmodified native API; retain inner timeout stdout/stderr."""
    from lab.verification import verify
    directory = new_run_directory("native")
    report = dict(status="INCOMPLETE", started=now(),run_directory=str(directory),
                  native_api_invoked=False,canonical_scientific_subprocess_executed=None)
    try:
        require_ready_source_review(project)
        report["native_api_invoked"] = True
        report["native_report"] = verify(project)
        report["status"] = report["native_report"]["status"]
        report["canonical_scientific_subprocess_executed"] = report["native_report"].get("mode") == "model-specific independent verifier"
    except subprocess.TimeoutExpired as exc:
        report.update(exception="TimeoutExpired: "+str(exc), timeout_seconds=exc.timeout)
        for name, body in (("stdout.txt", exc.stdout),("stderr.txt",exc.stderr)):
            text = body.decode("utf-8",errors="replace") if isinstance(body,bytes) else body or ""
            (directory/name).write_text(text,encoding="utf-8",newline="\n")
    except Exception as exc:
        report.update(status="FAIL",exception=type(exc).__name__+": "+str(exc))
    finally:
        report["finished"] = now()
        save(directory/"native-receipt.json",report)
    return report


def combined_assessment(native, supplement, native_items, evidence_paths):
    """Scientific assessment supplements the immutable legacy acceptance route."""
    errors=sum(supplement.get("error_counts",{}).values())
    failed=native.get("status")!="PASS" or supplement.get("status")=="FAIL" or errors>0
    coverage=supplement.get("status")=="CHECKS_COMPLETE"
    unresolved=supplement.get("stored_unresolved_rows",0)+supplement.get("unsupported_resolved_predicates",0)
    precision=[]
    for scenario,value in supplement.get("scenarios",{}).items():
        for field,statistic in value.get("paired",{}).items():
            if statistic.get("n",0)>0 and statistic.get("ci95") is not None and not statistic.get("precision_met"):
                precision.append(scenario+"."+field)
            elif statistic.get("precision_met") is False and statistic.get("n",0)>0:
                precision.append(scenario+"."+field)
    native_by_id={i["prediction_ref"]:i for i in native_items}
    if native_items and (set(native_by_id)!=set("P"+str(i) for i in range(1,8)) or any(i["verdict"]!="PASS" for i in native_items)):
        failed=True
    inconclusive=not coverage or unresolved>0 or bool(precision)
    verdict="FAIL" if failed else "INCONCLUSIVE" if inconclusive else "PASS"
    items=[]
    for i in range(1,8):
        items.append(dict(id="supplement-P"+str(i),prediction_ref="P"+str(i),
            method="Combined native receipts and independently recomputed planned finite-input checks; unresolved/unsupported coverage is retained",
            metric="source-reviewed finite coverage and original-constraint consistency",
            value=None,tolerance=dict(rate=RATE,split=SPLIT,objective=OBJECTIVE,scope="approved planned numerical regimes; not universal validation",unresolved=unresolved),
            verdict=verdict,triage="implementation-bug" if failed else "approximation-gap" if inconclusive else None,
            evidence_paths=evidence_paths))
    return dict(status=verdict,eligible_for_gate_request=verdict=="PASS",verification_items=items,
                native_acceptance_status=native.get("status"),supplement_status=supplement.get("status"),
                stored_and_unsupported_unresolved=unresolved,failed_precision=precision,
                full_scientific_validation=False,
                limitations=["Legacy native PASS is retained as its own receipt.","Combined assessment does not rewrite native or locked science.","Retained uncertainty is never promoted to scientific PASS.","Finite planned checks do not prove arbitrary real-input validity."])


def lineage_value(rows, recipe):
    """Executable independent conditional mean recipe, excluding undecided blocks explicitly."""
    from independent import finite_inputs,noma_adjudicate,oma_adjudicate,oma
    if recipe.get("op")!="independent_conditional_mean" or recipe.get("mask")!="independent_both_feasible" or recipe.get("column") not in {"sum_rate","oma_sum","paired_difference"}:
        raise ValueError("Unsupported executable lineage operation/mask/column")
    moment=Moments();count=unresolved=0
    for raw in rows:
        count+=1
        inputs=finite_inputs([float(raw[k]) for k in ("P","gw","gs","qw","qs")])
        ns=noma_adjudicate(inputs);os=oma_adjudicate(inputs)
        if "unresolved" in (ns["status"],os):
            unresolved+=1
            continue
        if ns["status"]!="feasible" or os!="feasible":continue
        if raw["status"]!="feasible":raise ValueError("Lineage raw classification contradicts original constraints")
        split=float(raw["a_star"])
        if not math.isfinite(split) or not 0<=split<=1:raise ValueError("Undefined accepted lineage split")
        nr=rates(inputs,split);od=oma(inputs)
        if nr["rw"]<inputs[3]-RATE or nr["rs"]<inputs[4]-RATE:raise ValueError("Lineage accepted split violates original constraints")
        values={"sum_rate":nr["sum_rate"],"oma_sum":od["oma_sum"],"paired_difference":nr["sum_rate"]-od["oma_sum"]}
        moment.add(values[recipe["column"]])
    return dict(value=moment.mean if moment.n else None,n=moment.n,rows=count,
                independently_unresolved_rows=unresolved,statistics=moment.summary(),
                status="INCONCLUSIVE" if unresolved or not moment.n else "COMPUTED")


def execute_lineage_recipe(project,recipe):
    require_ready_source_review(project)
    if len(set(recipe.get("source_manifests",[])))!=len(recipe.get("source_manifests",[])) or not recipe.get("source_manifests"):
        raise ValueError("Nonempty unique lineage source manifest list required")
    bindings={};raw_files=[]
    for name in recipe["source_manifests"]:
        file=within(project,name);m=verify_manifest(project,load(file))
        if m is None:
            from lab.models import RunManifest
            m=RunManifest.model_validate(load(file))
        raw=manifest_output(project,m,"channels.csv")
        bindings[name]=sha256(file);bindings[raw.relative_to(project).as_posix()]=sha256(raw)
        raw_files.append(raw)
    if bindings!=recipe["input_hashes"]:raise ValueError("Lineage recipe input binding mismatch")
    def rows():
        for file in raw_files:
            with file.open(encoding="utf-8",newline="") as stream:yield from csv.DictReader(stream)
    result=lineage_value(rows(),recipe)
    if result["rows"]!=recipe["rows"]:raise ValueError("Lineage planned row coverage mismatch")
    for name,digest in bindings.items():
        if sha256(within(project,name))!=digest:raise ValueError("Lineage input changed during execution")
    result.update(recipe=recipe,input_hashes=bindings,source_hashes=source_snapshot())
    return result


def write_lineage(project,items,summaries,directory):
    """Record executable recipes corresponding to actual independent streaming moments."""
    records=[]
    for scenario,summary in summaries.items():
        selected=[(file,m) for file,m in items if m["scenario"]==scenario]
        hashes={};paths=[]
        for file,m in selected:
            name=file.relative_to(project).as_posix();paths.append(name);hashes[name]=sha256(file)
            raw=next(o for o in m["outputs"] if Path(o["path"]).name=="channels.csv")
            hashes[raw["path"]]=raw["sha256"]
        for column,moment in summary["pairs"].items():
            recipe=dict(op="independent_conditional_mean",column=column,mask="independent_both_feasible",source_manifests=paths,input_hashes=hashes,rows=summary["total"])
            records.append(dict(key=scenario+"-"+column,unit="bit/s/Hz",recipe=recipe,value=moment.mean if moment.n else None,n=moment.n,independent_counts=summary["independent_counts"],
                                status="INCONCLUSIVE" if summary["independent_counts"]["unresolved"] or not moment.n else "COMPUTED",
                                statistics=moment.summary(),used_in=["P6 scenario-level analysis; native manuscript claims use only its supported operations"]))
    save(directory/"claim-lineage.json",dict(records=records,source_hashes=source_snapshot(),
        executable_command="python analysis/supplement/checker.py --lineage-recipe <project-relative-json-recipe>",
        denominator="independently resolved both-feasible blocks",undefined_denominator="null value, no substituted zero"))
