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
