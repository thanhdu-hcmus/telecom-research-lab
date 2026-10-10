"""Evidence checks, screened ranking and one-point weight sensitivity."""

from itertools import product

from lab.io import LabError, load, read_jsonl, save, within
from lab.models import IdeaCard


def eligible(card):
    return card.feasibility.passed and card.novelty.verdict in {
        "novel",
        "incremental-but-publishable",
    }


def weights_check(weights):
    if (
        set(weights) != {"thesis_fit", "time", "venue"}
        or any(type(v) is not int or v < 1 for v in weights.values())
        or sum(weights.values()) != 10
    ):
        raise LabError("Three positive integer weights must sum to ten")


def rank_cards(cards, weights):
    weights_check(weights)
    eligible, rejected = [], []
    for raw in cards:
        card = IdeaCard.model_validate(raw)
        if not card.feasibility.passed or card.novelty.verdict not in {
            "novel",
            "incremental-but-publishable",
        }:
            rejected.append(card.id)
            continue
        months = card.time_estimate_months
        expected_time = next((5 - i for i, t in enumerate([3, 4, 6, 9]) if months <= t), 1)
        if card.scores["time"].score != expected_time:
            raise LabError(f"Time score does not match estimate: {card.id}")
        eligible.append(
            {
                "id": card.id,
                "total": sum(weights[k] * card.scores[k].score for k in weights),
                "novelty": card.novelty.verdict,
                "risk_rating": card.risk_rating,
            }
        )
    if len({c["id"] for c in cards}) != len(cards):
        raise LabError("Duplicate idea IDs")
    eligible.sort(key=lambda c: (-c["total"], c["novelty"] != "novel", c["risk_rating"], c["id"]))
    return {"status": "PASS", "ranked": eligible, "rejected": rejected}


def sensitivity_cards(cards, weights):
    base = [c["id"] for c in rank_cards(cards, weights)["ranked"][:3]]
    variations = []
    keys = list(weights)
    # Joint +/-1 perturbations preserving total ten; report their top-three changes.
    for offsets in product([-1, 0, 1], repeat=3):
        changed = {k: weights[k] + d for k, d in zip(keys, offsets)}
        if any(v < 1 for v in changed.values()) or sum(changed.values()) != 10:
            continue
        top = [c["id"] for c in rank_cards(cards, changed)["ranked"][:3]]
        variations.append({"weights": changed, "top_three": top, "changed": top != base})
    return {"status": "PASS", "base_top_three": base, "variations": variations}


def cards_at(path):
    return [load(p) for p in sorted((path / "ideas").glob("*.yaml")) if p.name != "novelty.yaml"]


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
    result = rank_cards(cards, load(path.parents[1] / "config/ranking.yaml")["weights"])
    if not result["ranked"]:
        raise LabError("No idea passes feasibility and novelty screens")
    weights = load(path.parents[1] / "config/ranking.yaml")["weights"]
    if load(path / "ideas/ranking.json") != result or load(
        path / "ideas/sensitivity.json"
    ) != sensitivity_cards(cards, weights):
        raise LabError("Regenerate ranking/sensitivity from current cards and weights")
    return result


def ranking(path, sensitivity=False):
    from lab.state import ensure_phase

    ensure_phase(path, "P3")
    weights = load(path.parents[1] / "config/ranking.yaml")["weights"]
    result = (
        sensitivity_cards(cards_at(path), weights)
        if sensitivity
        else rank_cards(cards_at(path), weights)
    )
    save(path / ("ideas/sensitivity.json" if sensitivity else "ideas/ranking.json"), result)
    if not sensitivity:
        (path / "ideas/ranking.md").write_text(
            "# Screened ranking\n\n"
            + "\n".join(
                f"{i}. {c['id']}: {c['total']}/50" for i, c in enumerate(result["ranked"], 1)
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result
