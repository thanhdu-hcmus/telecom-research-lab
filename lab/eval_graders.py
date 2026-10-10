"""Deterministic acceptance thresholds; no LLM grading or self-reported passes."""

from lab.models import PaperCard


def grade_task(name, output, workspace, expected):
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
