import pytest

from lab.ideas import rank_cards, sensitivity_cards
from lab.io import LabError


def card(id="I1", novelty="novel", fit=5, risk=2):
    return dict(
        id=id,
        title="Probe",
        problem="Problem",
        gap_refs=["G1"],
        closest_works=[dict(id=f"P{i}", delta="Delta") for i in range(3)],
        method_sketch="Method",
        expected_contributions=["Conjecture"],
        risks=["Risk"],
        risk_rating=risk,
        resources={"compute_estimate": "CPU 1h"},
        time_estimate_months=3,
        target_venue_class="Q3",
        feasibility={"pass": True, "reasons": ["Tractable"]},
        novelty={"verdict": novelty, "report": "ideas/novelty/I1.yaml"},
        scores={
            k: dict(score=v, rationale="Evidence", evidence=["P0", "P1"])
            for k, v in {"thesis_fit": fit, "time": 5, "venue": 5}.items()
        },
    )


def test_scores_screens_and_ties():
    result = rank_cards(
        [card("B", risk=3), card("A"), card("C", "already-done")],
        dict(thesis_fit=5, time=3, venue=2),
    )
    assert result["ranked"][0] == dict(id="A", total=50, novelty="novel", risk_rating=2)
    assert result["rejected"] == ["C"]
    assert (
        rank_cards(
            [card("X", "incremental-but-publishable"), card("Y")],
            dict(thesis_fit=5, time=3, venue=2),
        )["ranked"][0]["id"]
        == "Y"
    )


def test_weights_time_and_sensitivity():
    with pytest.raises(LabError):
        rank_cards([card()], dict(thesis_fit=5, time=3, venue=3))
    bad = card()
    bad["time_estimate_months"] = 10
    with pytest.raises(LabError):
        rank_cards([bad], dict(thesis_fit=5, time=3, venue=2))
    report = sensitivity_cards([card()], dict(thesis_fit=5, time=3, venue=2))
    assert len(report["variations"]) == 7
    assert not any(v["changed"] for v in report["variations"])


def test_dry_run_accepts_established_methods_without_claiming_novelty():
    weights = dict(thesis_fit=5, time=3, venue=2)
    established = card("KNOWN", "already-done")
    assert not rank_cards([established], weights)["ranked"]
    result = rank_cards([established, card("UNKNOWN", "unclear")], weights, dry_run=True)
    assert result["ranked"][0]["novelty"] == "already-done"
    assert result["rejected"] == ["UNKNOWN"]
    assert sensitivity_cards([established], weights, dry_run=True)["base_top_three"] == ["KNOWN"]


def test_ranking_config_controls_thresholds_novelty_and_ties():
    from lab.ideas import ranking_policy

    policy = ranking_policy().copy()
    weights = policy["weights"]
    policy["allowed_novelty"] = ["novel"]
    assert rank_cards([card("INC", "incremental-but-publishable")], weights, policy=policy)[
        "rejected"
    ] == ["INC"]
    policy["time_thresholds_months"] = [1, 2, 4, 6]
    changed = card()
    changed["scores"]["time"]["score"] = 3
    assert rank_cards([changed], weights, policy=policy)["ranked"][0]["total"] == 44
    policy["time_thresholds_months"] = [3, 4, 6, 9]
    policy["tie_breakers"] = ["id", "risk_rating"]
    assert (
        rank_cards([card("A", risk=5), card("B", risk=1)], weights, policy=policy)["ranked"][0][
            "id"
        ]
        == "A"
    )
    policy["allowed_novelty"] = ["already-done"]
    with pytest.raises(LabError, match="publishable"):
        rank_cards([card()], weights, policy=policy)


def test_reproduction_selection_contract_and_reference(tmp_path):
    from pathlib import Path

    from lab.ideas import cards_at, validate_reproduction
    from lab.io import load, save, write_jsonl
    from lab.models import ReproductionSelection

    selection = dict(
        id="R1",
        reference_id="doi:fixture",
        purpose="reproduce-and-ablate",
        reference_figures=["Fig. 2"],
        ablation="Disable optimized allocation",
        expected_outputs=["Overlay and ablation"],
        code_status="official-code",
        code_revision="a" * 40,
        data_availability="Synthetic channel samples; no third-party dataset",
    )
    with pytest.raises(ValueError, match="pinned"):
        ReproductionSelection.model_validate({**selection, "code_revision": None})
    save(tmp_path / "ideas/reproduction.yaml", selection)
    (tmp_path / "ideas/reproduction-plan.md").write_text(
        "# Reproduce Fig. 2 and ablate allocation\n", encoding="utf-8"
    )
    assert not cards_at(tmp_path)
    with pytest.raises(LabError, match="reviewed literature"):
        validate_reproduction(tmp_path)
    write_jsonl(tmp_path / "literature/candidates.jsonl", [{"id": "doi:fixture"}])
    reference = load(Path(__file__).resolve().parents[1] / "fixtures/m4-gold-cards.yaml")[0]
    reference["id"] = "doi:fixture"
    reference["key_results"] = ["Synthetic fixture result for contract validation only"]
    reference["grounding"]["key_results"] = [
        {"source": "synthetic fixture", "page": 1, "location": "Results"}
    ]
    save(tmp_path / "literature/cards/reference.yaml", reference)
    assert validate_reproduction(tmp_path)["selection"] == "R1"
    reference["key_results"] = None
    save(tmp_path / "literature/cards/reference.yaml", reference)
    with pytest.raises(LabError, match="reference results"):
        validate_reproduction(tmp_path)
