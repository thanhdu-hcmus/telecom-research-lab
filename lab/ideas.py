"""Evidence checks, screened ranking and one-point weight sensitivity."""

import math
from itertools import product
from pathlib import Path

from lab.io import LabError, load, read_jsonl, save, within
from lab.models import IdeaCard, PaperCard, ReproductionSelection


def ranking_policy(policy=None):
    policy = (
        policy
        if policy is not None
        else load(Path(__file__).resolve().parents[1] / "config/ranking.yaml")
    )
    thresholds = policy["time_thresholds_months"]
    if (
        len(thresholds) != 4
        or any(type(t) not in {int, float} or not math.isfinite(t) or t <= 0 for t in thresholds)
        or thresholds != sorted(set(thresholds))
    ):
        raise LabError("Ranking needs four increasing positive month thresholds")
    if policy["maximum_score"] != 50:
        raise LabError("Maximum score must be 50 for five-point rubrics and weights totaling ten")
    allowed = policy["allowed_novelty"]
    if not allowed or not set(allowed) <= {"novel", "incremental-but-publishable"}:
        raise LabError("Research ranking may allow only supported publishable novelty verdicts")
    ties = policy["tie_breakers"]
    if len(set(ties)) != len(ties) or not set(ties) <= {"novelty", "risk_rating", "id"}:
        raise LabError("Unknown or duplicate ranking tie breaker")
    return policy


def eligible(card, *, dry_run=False, policy=None):
    allowed = set(ranking_policy(policy)["allowed_novelty"])
    if dry_run:
        allowed.add("already-done")
    return card.feasibility.passed and card.novelty.verdict in allowed


def weights_check(weights):
    if (
        set(weights) != {"thesis_fit", "time", "venue"}
        or any(type(v) is not int or v < 1 for v in weights.values())
        or sum(weights.values()) != 10
    ):
        raise LabError("Three positive integer weights must sum to ten")


def rank_cards(cards, weights, *, policy=None, dry_run=False):
    weights_check(weights)
    policy = ranking_policy(policy)
    ranked, rejected = [], []
    for raw in cards:
        card = IdeaCard.model_validate(raw)
        if not eligible(card, policy=policy, dry_run=dry_run):
            rejected.append(card.id)
            continue
        months = card.time_estimate_months
        expected_time = next(
            (5 - i for i, t in enumerate(policy["time_thresholds_months"]) if months <= t), 1
        )
        if card.scores["time"].score != expected_time:
            raise LabError(f"Time score does not match estimate: {card.id}")
        ranked.append(
            {
                "id": card.id,
                "total": sum(weights[k] * card.scores[k].score for k in weights),
                "novelty": card.novelty.verdict,
                "risk_rating": card.risk_rating,
            }
        )
    if len({c["id"] for c in cards}) != len(cards):
        raise LabError("Duplicate idea IDs")
    novelty_order = {"novel": 0, "incremental-but-publishable": 1, "already-done": 2}

    def sort_key(c):
        values = {
            "novelty": novelty_order[c["novelty"]],
            "risk_rating": c["risk_rating"],
            "id": c["id"],
        }
        return (-c["total"], *(values[k] for k in policy["tie_breakers"]), c["id"])

    ranked.sort(key=sort_key)
    return {"status": "PASS", "ranked": ranked, "rejected": rejected}


def sensitivity_cards(cards, weights, *, policy=None, dry_run=False):
    policy = ranking_policy(policy)
    base = [
        c["id"] for c in rank_cards(cards, weights, policy=policy, dry_run=dry_run)["ranked"][:3]
    ]
    variations = []
    keys = list(weights)
    # Joint +/-1 perturbations preserving total ten; report their top-three changes.
    for offsets in product([-1, 0, 1], repeat=3):
        changed = {k: weights[k] + d for k, d in zip(keys, offsets)}
        if any(v < 1 for v in changed.values()) or sum(changed.values()) != 10:
            continue
        top = [
            c["id"]
            for c in rank_cards(cards, changed, policy=policy, dry_run=dry_run)["ranked"][:3]
        ]
        variations.append({"weights": changed, "top_three": top, "changed": top != base})
    return {"status": "PASS", "base_top_three": base, "variations": variations}


def cards_at(path):
    return [
        load(p)
        for p in sorted((path / "ideas").glob("*.yaml"))
        if p.name not in {"novelty.yaml", "reproduction.yaml"}
    ]


def validate_reproduction(path):
    selection = ReproductionSelection.model_validate(load(path / "ideas/reproduction.yaml"))
    ids = {c["id"] for c in read_jsonl(path / "literature/candidates.jsonl")}
    if selection.reference_id not in ids:
        raise LabError("Reproduction reference must be in the reviewed literature")
    cards = [
        PaperCard.model_validate(load(p))
        for p in sorted((path / "literature/cards").glob("*.yaml"))
        if load(p).get("id") == selection.reference_id
    ]
    if len(cards) != 1 or not cards[0].key_results:
        raise LabError("Reproduction requires a grounded full-paper card with reference results")
    plan = path / "ideas/reproduction-plan.md"
    if not plan.is_file() or not plan.read_text(encoding="utf-8").strip():
        raise LabError("Reproduction requires a written figure, data and ablation plan")
    return {"status": "PASS", "selection": selection.id, "reference_id": selection.reference_id}


def validate_ideas(path):
    cards = cards_at(path)
    if len(cards) < 15:
        raise LabError("G3 requires at least fifteen complete idea cards")
    ids = {c["id"] for c in read_jsonl(path / "literature/candidates.jsonl")}
    for raw in cards:
        c = IdeaCard.model_validate(raw)
        if not {w.id for w in c.closest_works} <= ids or not set(c.scores["venue"].evidence) <= ids:
            raise LabError(f"Unknown closest work or venue comparator: {c.id}")
        report = load(within(path, c.novelty.report))
        queries = report.get("queries", [])
        if len({q.get("query") for q in queries}) < 5 or not any(
            q.get("source") == "web" for q in queries
        ):
            raise LabError(
                f"Novelty report needs five distinct targeted queries including web: {c.id}"
            )
        if not any(
            q.get("source") in {"openalex", "crossref", "arxiv", "semanticscholar", "ieee"}
            for q in queries
        ):
            raise LabError("Novelty audit needs scholarly searches as well as web")
        if not all(q.get("source") and q.get("timestamp") and q.get("evidence") for q in queries):
            raise LabError("Novelty searches need dated source/evidence receipts")
        if report.get("verdict") != c.novelty.verdict:
            raise LabError("Card and novelty report verdict differ")
    policy = ranking_policy(load(path.parents[1] / "config/ranking.yaml"))
    weights = policy["weights"]
    dry_run = load(path / "scope.yaml", {}).get("mode") == "dry-run"
    result = rank_cards(cards, weights, policy=policy, dry_run=dry_run)
    if not result["ranked"]:
        raise LabError("No idea passes feasibility and novelty screens")
    if load(path / "ideas/ranking.json") != result or load(
        path / "ideas/sensitivity.json"
    ) != sensitivity_cards(cards, weights, policy=policy, dry_run=dry_run):
        raise LabError("Regenerate ranking/sensitivity from current cards and weights")
    return result


def ranking(path, sensitivity=False):
    from lab.state import ensure_phase

    ensure_phase(path, "P3")
    if load(path / "scope.yaml", {}).get("workflow") == "reproduction":
        raise LabError("Use a reproduction selection and plan for this workflow, not idea ranking")
    policy = ranking_policy(load(path.parents[1] / "config/ranking.yaml"))
    weights = policy["weights"]
    dry_run = load(path / "scope.yaml", {}).get("mode") == "dry-run"
    result = (
        sensitivity_cards(cards_at(path), weights, policy=policy, dry_run=dry_run)
        if sensitivity
        else rank_cards(cards_at(path), weights, policy=policy, dry_run=dry_run)
    )
    save(path / ("ideas/sensitivity.json" if sensitivity else "ideas/ranking.json"), result)
    if not sensitivity:
        (path / "ideas/ranking.md").write_text(
            "# Screened ranking\n\n"
            + (
                "Dry-run benchmark only; established methods are eligible without a novelty claim.\n\n"
                if dry_run
                else ""
            )
            + "\n".join(
                f"{i}. {c['id']}: {c['total']}/50" for i, c in enumerate(result["ranked"], 1)
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result
