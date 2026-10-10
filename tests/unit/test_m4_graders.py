from pathlib import Path

from lab.eval_graders import grade_task
from lab.io import load

ROOT = Path(__file__).resolve().parents[2]


def test_card_grader_gold_and_fabrication(tmp_path):
    expected = load(ROOT / "tests/evals/card-grounding/expected.yaml")
    gold = expected["gold_cards"]
    assert grade_task("card-grounding", {"cards": gold}, tmp_path, expected)["passed"]
    bad = [{**g, "system": {"users": 2}} for g in gold]
    result = grade_task("card-grounding", {"cards": bad}, tmp_path, expected)
    assert not result["passed"]
    assert result["fabricated"]


def test_gap_and_code_graders(tmp_path):
    expected = load(ROOT / "tests/evals/gap-evidence/expected.yaml")
    gap = {
        "id": "G1",
        "near_miss_ids": expected["card_ids"][:2],
        "missing": "CSI not reported",
        "evidence": ["cards/P1.yaml", "cards/P2.yaml"],
    }
    assert grade_task("gap-evidence", {"gaps": [gap]}, tmp_path, expected)["passed"]
    gap["near_miss_ids"] = ["invented", "missing"]
    assert not grade_task("gap-evidence", {"gaps": [gap]}, tmp_path, expected)["passed"]
    expected = load(ROOT / "tests/evals/code-scout-discrimination/expected.yaml")
    reply = {
        "candidates": list(expected["candidates"]),
        "rejections": [
            {"id": i, "reason": "tutorial or missing paper evidence"}
            for i in expected["rejections"]
        ],
        "acceptance_status": "reproduction-pending",
    }
    assert grade_task("code-scout-discrimination", reply, tmp_path, expected)["passed"]
    reply["candidates"].append("tutorial-d")
    assert not grade_task("code-scout-discrimination", reply, tmp_path, expected)["passed"]


def test_recall_threshold(tmp_path):
    expected = load(ROOT / "tests/evals/lit-recall/expected.yaml")
    for count in [7, 8, 10]:
        reply = {
            "screening": [{"id": i, "decision": "include"} for i in expected["key_ids"][:count]]
        }
        assert grade_task("lit-recall", reply, tmp_path, expected)["passed"] == (count >= 8)
