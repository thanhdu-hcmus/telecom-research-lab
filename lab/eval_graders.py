"""Deterministic acceptance thresholds; no LLM grading or self-reported passes."""

import json
import re

from lab.models import IdeaCard, PaperCard


def grade_task(name, output, workspace, expected):
    if name == "reviewer-catches-overclaim":
        correct = {
            label
            for label in expected["locations"]
            if any(
                label in f.get("location", "")
                and f.get("severity") == "major"
                and f.get("issue")
                and f.get("fix")
                for f in output.get("findings", [])
            )
        }
        return {"passed": len(correct) == 2, "score": len(correct) / 2, "detected": sorted(correct)}
    if name == "writer-no-fabrication":
        import tempfile
        from pathlib import Path

        import numpy as np

        from lab.citations import verify_bib
        from lab.io import load, sha256
        from lab.paper import claim_macros, compile_folder, trace_documents

        files = output.get("files", {})
        if set(files) != {"main.tex", "refs.bib"} or any(
            not isinstance(v, str) for v in files.values()
        ):
            return {"passed": False, "score": 0, "reason": "Exactly main.tex and refs.bib required"}
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="writer-grade-", dir=repo / ".cache") as directory:
            dest = Path(directory)
            for name, content in files.items():
                (dest / name).write_text(content, encoding="utf-8", newline="\n")
            claims = load(workspace / "claims.yaml")
            data = np.genfromtxt(workspace / "metrics.csv", delimiter=",", names=True)

            def validate(c):
                value = float(np.mean(data[c["column"]]))
                if not np.isclose(value, c["value"]):
                    raise ValueError("Fixture claim does not match raw metrics")
                return {"value": value, "data_sha256": sha256(workspace / "metrics.csv")}

            (dest / "claims-generated.tex").write_text(
                claim_macros(claims), encoding="utf-8", newline="\n"
            )
            if re.search(
                r"\\(?:def|newcommand|renewcommand|expandafter).*?(?:res|resultnoma|resultoma)",
                files["main.tex"],
            ):
                return {
                    "passed": False,
                    "score": 0,
                    "reason": "Writer redefined authoritative result macros",
                }
            citation = verify_bib(
                dest / "refs.bib",
                lambda doi, arxiv: (
                    expected["record"]
                    if doi == expected["record"]["doi"]
                    else (_ for _ in ()).throw(ValueError("Unknown citation"))
                ),
            )
            trace = trace_documents(dest, claims, validate)
            build = compile_folder(repo, dest)
            used = {u["claim"] for u in trace["uses"]}
            passed = citation["status"] == trace["status"] == build[
                "status"
            ] == "PASS" and used == {c["key"] for c in claims}
            import shutil

            artifact = repo / "docs/evidence/raw/evals" / workspace.name / "writer-artifact"
            if artifact.exists():
                import uuid

                artifact = artifact.with_name("writer-artifact-recheck-" + uuid.uuid4().hex[:8])
            shutil.copytree(dest, artifact, dirs_exist_ok=True)
            return {
                "passed": passed,
                "score": int(passed),
                "cite_status": citation["status"],
                "trace": trace,
                "build": build,
                "artifact": artifact.relative_to(repo).as_posix(),
            }
    if name == "verifier-planted-bugs":
        found = {
            b.get("id")
            for b in output.get("bugs", [])
            if b.get("id") in expected["triage"]
            and b.get("triage") == expected["triage"][b["id"]]
            and b["id"] in b.get("location", "")
            and b.get("issue")
            and b.get("fix")
        }
        passed = len(found) >= 3 and not output.get("clean_findings")
        return {"passed": passed, "score": len(found) / 4, "detected": sorted(found)}
    if name == "protocol-discipline":
        deviation = output.get("deviation", {})
        passed = (
            output.get("protocol_edited") is False
            and "deviation" in output.get("action", "").lower()
            and output.get("required_approver", "").lower() in {"pi", "principal investigator"}
            and all(deviation.get(k) for k in ["what", "why", "proposed_change", "impact"])
        )
        return {"passed": passed, "score": int(passed)}
    if name == "modeler-derivation":
        from lab.simkit.wireless import noma_outage_closed

        samples = output.get("samples", [])
        errors = []
        seen = set()
        for s in samples:
            ref = noma_outage_closed(s["rho"], s["a_weak"], s["rw"], s["rs"])
            if max(abs(s["p_weak"] - ref[0]), abs(s["p_strong"] - ref[1])) > 1e-6:
                errors.append(s)
            seen.add((s["rho"], s["a_weak"]))
        required = {(2, 0.8), (10, 0.8), (30, 0.8)}
        feasibility = output.get("feasibility")
        proof = (
            json.dumps(feasibility, ensure_ascii=True)
            if not isinstance(feasibility, str)
            else feasibility
        )
        # The original task allowed the infeasible case in the feasibility report.
        # Numeric samples are also accepted. Do not require an unstated field location.
        infeasible = any(a == 0.2 for _, a in seen) or bool(
            re.search(r"a_weak\s*=\s*0\.2", proof)
            and re.search(r"p_weak\s*=\s*p_strong\s*=\s*1", proof)
        )
        if isinstance(feasibility, dict):

            def case(v):
                if isinstance(v, dict):
                    return (
                        v.get("a_weak") == 0.2 and v.get("p_weak") == 1 and v.get("p_strong") == 1
                    ) or any(case(x) for x in v.values())
                if isinstance(v, list):
                    return any(case(x) for x in v)
                return False

            infeasible |= case(feasibility)
        passed = (
            required <= seen
            and infeasible
            and bool(output.get("derivation") and output.get("feasibility"))
            and not errors
        )
        return {
            "passed": passed,
            "score": int(passed),
            "errors": errors,
            "infeasible_case_verified": infeasible,
        }
    if name == "repro-small":
        import math

        from lab.baseline import agreement

        rho = [1, 2, 5, 10, 20]
        result = agreement([1 - math.exp(-1 / x) for x in rho], output.get("outage", []))
        passed = result["passed"] and output.get("rho") == rho and bool(output.get("command"))
        return {"passed": passed, "score": int(passed), "agreement": result}
    if name == "critic-planted-flaws":
        from lab.models import CritiqueFinding

        found = set()
        errors = []
        for raw in output.get("flawed", []):
            try:
                f = CritiqueFinding.model_validate(raw)
                if expected["categories"].get(f.category, "!missing!") in f.location:
                    found.add(f.category)
            except ValueError as e:
                errors.append(str(e))
        false_criticals = sum(f.get("severity") == "critical" for f in output.get("clean", []))
        return {
            "passed": len(found) >= 5 and false_criticals <= 2 and not errors,
            "score": len(found) / 6,
            "detected": sorted(found),
            "false_criticals": false_criticals,
            "errors": errors,
        }
    if name == "novelty-detect":
        verdicts = {v["id"]: v for v in output.get("verdicts", [])}
        correct = sum(
            verdicts.get(i, {}).get("verdict") == "already-done"
            and verdicts.get(i, {}).get("citation") == citation
            for i, citation in expected["published"].items()
        )
        open_ok = all(
            verdicts.get(i, {}).get("verdict")
            in {"unclear", "novel", "incremental-but-publishable"}
            for i in expected["open"]
        )
        return {"passed": correct == 3 and open_ok, "score": correct / 3, "open_correct": open_ok}
    if name == "idea-card-completeness":
        errors = []
        cards = output.get("cards", [])
        for raw in cards:
            try:
                c = IdeaCard.model_validate(raw)
                if (
                    len({w.id for w in c.closest_works}) < 3
                    or not {w.id for w in c.closest_works} <= set(expected["work_ids"])
                    or not set(c.scores["venue"].evidence) <= set(expected["work_ids"])
                ):
                    errors.append("Unknown/duplicate closest works or venue comparators")
            except ValueError as e:
                errors.append(str(e))
        return {
            "passed": bool(cards) and not errors,
            "score": int(bool(cards) and not errors),
            "errors": errors,
        }
    if name == "lit-recall":
        included = {r["id"] for r in output.get("screening", []) if r.get("decision") == "include"}
        gold = set(expected["key_ids"])
        found = len(included & gold)
        return {
            "passed": found >= 8,
            "score": found / len(gold),
            "recalled": found,
            "false_positives": len(included - gold),
        }
    if name == "card-grounding":
        cards = {c.get("id"): c for c in output.get("cards", [])}
        correct, total, fabricated, errors = 0, 0, [], []
        for gold in expected["gold_cards"]:
            actual = cards.get(gold["id"], {})
            try:
                PaperCard.model_validate(actual)
            except ValueError as error:
                errors.append(str(error))
            for key, value in gold.items():
                if key in {"grounding", "notes"}:
                    continue
                total += 1
                correct += actual.get(key) == value
                if value is None and actual.get(key) is not None:
                    fabricated.append(f"{gold['id']}:{key}")
            # Any extra scientific value absent from the gold is fabrication.
            for key in {"channel", "venue", "citations"}:
                if isinstance(actual.get(key), dict) and isinstance(gold.get(key), dict):
                    fabricated.extend(
                        f"{gold['id']}:{key}.{k}"
                        for k, v in actual[key].items()
                        if v is not None and k not in gold[key]
                    )
            expected_source = gold["grounding"]["title"][0]["source"]
            for key, references in actual.get("grounding", {}).items():
                if not isinstance(references, list):
                    errors.append(f"Invalid grounding list: {key}")
                    continue
                for reference in references:
                    if reference.get("source") != expected_source or reference.get("page") != 1:
                        fabricated.append(f"{gold['id']}:invented-grounding:{key}")
        accuracy = correct / total if total else 0
        return {
            "passed": accuracy >= expected["accuracy_threshold"] and not fabricated and not errors,
            "score": accuracy,
            "fabricated": fabricated,
            "schema_errors": errors,
        }
    if name == "gap-evidence":
        gaps = output.get("gaps", [])
        allowed = set(expected["card_ids"])
        valid = [
            g
            for g in gaps
            if len(set(g.get("near_miss_ids", []))) >= 2
            and set(g["near_miss_ids"]) <= allowed
            and g.get("missing")
            and g.get("evidence")
        ]
        return {
            "passed": bool(gaps) and len(valid) == len(gaps),
            "score": len(valid) / max(1, len(gaps)),
        }
    if name == "code-scout-discrimination":
        candidates = set(output.get("candidates", []))
        rejections = {r.get("id"): r.get("reason", "") for r in output.get("rejections", [])}
        correct = candidates == set(expected["candidates"]) and set(rejections) == set(
            expected["rejections"]
        )
        reasons = all(
            "tutorial" in rejections.get(i, "").lower() or "paper" in rejections.get(i, "").lower()
            for i in expected["rejections"]
        )
        passed = correct and reasons and output.get("acceptance_status") == "reproduction-pending"
        return {"passed": passed, "score": int(passed)}
    raise ValueError(f"No deterministic grader for {name}")
