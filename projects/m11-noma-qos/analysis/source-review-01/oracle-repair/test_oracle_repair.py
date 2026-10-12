"""Synthetic replay regressions; definitions can be copied into supplement tests."""

import copy
import math
import sys
from pathlib import Path

import pytest

SUPPLEMENT = Path(__file__).resolve().parents[2] / "supplement"
sys.path.insert(0, str(SUPPLEMENT))

from independent import OBJECTIVE, RATE, SPLIT, Audit, rates  # noqa: E402
from replay import check_oracle_original, load_shared, recursive_compare, replay_job  # noqa: E402


def oracle_fixture(inputs, split=1.0, status="feasible", **policy):
    """Complete synthetic solver record, with directly recomputed attempted rates."""
    record = dict(
        status=status,
        feasible=1.0 if status == "feasible" else 0.0 if status == "infeasible" else None,
        feasibility_certificate="synthetic",
        optimality_status="numerical-concavity-bound"
        if status == "feasible"
        else "not-established",
        a_star=None,
        candidate_a=None,
        exact_split="",
        rw=None,
        rs=None,
        sum_rate=None,
        residual_w=None,
        residual_s=None,
        sic_residual=None,
        objective_upper_bound=None,
        objective_gap_bound=None,
        root_iterations=0,
        optimizer_iterations=0,
        optimizer_evaluations=0,
        singleton=False,
        inner_lower=None,
        inner_upper=None,
        outer_lower=None,
        outer_upper=None,
        reason="synthetic isolated fixture",
        rate_tolerance=RATE,
        split_tolerance=SPLIT,
        objective_tolerance=OBJECTIVE,
        max_root_iterations=96,
        max_optimizer_iterations=256,
    )
    record.update(policy)
    p, w, s, qw, qs = inputs
    record.update(
        oma_rw=math.log2(1 + p * w) / 2,
        oma_rs=math.log2(1 + p * s) / 2,
        oma_sum=(math.log2(1 + p * w) + math.log2(1 + p * s)) / 2,
    )
    if split is not None:
        r = rates(inputs, split)
        record.update(candidate_a=split, **{"candidate_" + k: v for k, v in r.items()})
        record.update(
            residual_w=r["rw"] - qw,
            residual_s=r["rs"] - qs,
            sic_residual=r["cw_at_s"] - r["rw"],
            objective_upper_bound=r["sum_rate"],
            objective_gap_bound=0.0,
        )
        if status == "feasible":
            record.update(a_star=split, **r)
    return record


def synthetic_replay(base_split=1.0, tighter_split=1.0, status="feasible", inputs=None):
    inputs = inputs or [1.0, 1.0, 4.0, 0.0, 0.0]
    params = dict(
        oracle_rows=1,
        sensitivity_rows=1,
        rate_tolerance=RATE,
        split_tolerance=SPLIT,
        objective_tolerance=OBJECTIVE,
    )
    raw = dict(zip(("P", "gw", "gs", "qw", "qs"), map(str, inputs)))
    raw.update(status="feasible", sum_rate=str(math.log2(5)))

    def solve(*values, **policy):
        split = base_split if policy["rate_tolerance"] == RATE else tighter_split
        return oracle_fixture(values, split, status, **policy)

    base = solve(*inputs, rate_tolerance=RATE, split_tolerance=SPLIT, objective_tolerance=OBJECTIVE)
    tight = solve(
        *inputs,
        rate_tolerance=RATE / 10,
        split_tolerance=SPLIT / 10,
        objective_tolerance=OBJECTIVE / 10,
    )
    checks = [
        dict(
            row=0,
            inputs=inputs,
            analytic_status="feasible",
            analytic_sum=math.log2(5),
            oracle=base,
            tighter_oracle=tight,
        )
    ]
    return checks, [raw], params, solve


def test_feasible_indicator_drift_fails_exactly():
    audit = Audit()
    recursive_compare(audit, "oracle.feasible", 1.0 - RATE / 2, 1.0, 0)
    assert "oracle.feasible" in audit.counts


@pytest.mark.parametrize("status", ["infeasible", "unresolved"])
def test_nonaccepted_final_rate_is_not_an_attempted_rate(status):
    record = oracle_fixture([1, 1, 4, 0, 0], 0.25, status)
    record["sum_rate"] = record["candidate_sum_rate"]
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert "oracle.sum_rate.mask" in audit.counts


def test_absent_attempt_cannot_keep_candidate_rate():
    record = oracle_fixture([1, 1, 4, 0, 0], None, "unresolved")
    record["candidate_rw"] = 0.0
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert "oracle.candidate_rw.mask" in audit.counts


def test_shared_reproduction_does_not_endorse_poor_accepted_optimum():
    args = synthetic_replay(0.25, 0.25)
    audit = Audit()
    result = replay_job(*args, audit)
    assert "oracle.agreement.analytic_base.objective" in audit.counts
    assert "oracle.agreement.base_independent.objective" in audit.counts
    assert result["comparisons"]["analytic_base"]["objective_max_residual"] > 0.6


def test_direct_base_tighter_sensitivity_is_a_separate_comparison():
    args = synthetic_replay(1.0, 0.75)
    audit = Audit()
    result = replay_job(*args, audit)
    assert "oracle.agreement.base_tighter.objective" in audit.counts
    assert result["comparisons"]["base_tighter"]["accepted_objectives"] == 1


def test_resolved_classification_conflict_fails():
    args = synthetic_replay(None, None, "infeasible")
    audit = Audit()
    replay_job(*args, audit)
    assert "oracle.agreement.analytic_base.status" in audit.counts
    assert "oracle.agreement.base_independent.status" in audit.counts


def test_unresolved_replay_preserves_uncertainty_and_transitions():
    checks, raw, params, solve = synthetic_replay(None, 1.0, "unresolved")

    def transition_solver(*values, **policy):
        return (
            oracle_fixture(values, None, "unresolved", **policy)
            if policy["rate_tolerance"] == RATE
            else oracle_fixture(values, 1.0, **policy)
        )

    checks[0]["tighter_oracle"] = transition_solver(
        *checks[0]["inputs"],
        rate_tolerance=RATE / 10,
        split_tolerance=SPLIT / 10,
        objective_tolerance=OBJECTIVE / 10,
    )
    audit = Audit()
    result = replay_job(checks, raw, params, transition_solver, audit)
    assert result["base_statuses"] == {"unresolved": 1}
    assert result["tighter_statuses"] == {"feasible": 1}
    assert result["statuses"] == {"unresolved": 1, "feasible": 1}
    assert result["unresolved_counts"]["base"] == 1
    assert result["optimality_not_established_counts"]["base"] == 1
    assert result["classification_transitions"] == {"unresolved->feasible": 1}
    assert audit.ok(), audit.errors


def test_tighter_gap_acceptance_uses_tighter_policy():
    checks, raw, params, solve = synthetic_replay()
    checks[0]["tighter_oracle"]["objective_gap_bound"] = OBJECTIVE / 2

    def oversized_gap(*values, **policy):
        record = solve(*values, **policy)
        if policy["rate_tolerance"] < RATE:
            record["objective_gap_bound"] = OBJECTIVE / 2
        return record

    audit = Audit()
    replay_job(checks, raw, params, oversized_gap, audit)
    assert "tighter_oracle.objective_gap_bound.acceptance" in audit.counts


def test_unsupported_independent_boundary_stays_explicit(monkeypatch):
    import replay

    monkeypatch.setattr(
        replay,
        "noma_adjudicate",
        lambda inputs: dict(
            status="unresolved", certificate="synthetic unsupported boundary", low=None, high=None
        ),
    )
    audit = Audit()
    result = replay_job(*synthetic_replay(), audit)
    assert result["unresolved_counts"]["independent"] == 1
    assert result["optimality_not_established_counts"]["independent"] == 1
    assert any(a.get("method") == "independent-oracle-comparison" for a in audit.ambiguities)
    assert audit.ok(), audit.errors


def test_budget_guard_stops_replay_with_deadline_failure():
    checks, raw, params, solve = synthetic_replay()

    def deadline():
        raise TimeoutError("synthetic replay deadline")

    with pytest.raises(TimeoutError, match="synthetic replay deadline"):
        replay_job(copy.deepcopy(checks), raw, params, solve, Audit(), budget_check=deadline)


def test_shared_solver_round_trip_is_only_labelled_reproduction():
    checks, raw, params, _ = synthetic_replay()
    solve = load_shared(SUPPLEMENT.parents[1] / "sim" / "src" / "oracle.py")
    inputs = checks[0]["inputs"]
    for key, factor in (("oracle", 1), ("tighter_oracle", 10)):
        policy = {
            k: params[k] / factor
            for k in ("rate_tolerance", "split_tolerance", "objective_tolerance")
        }
        result = solve(*inputs, **policy)
        checks[0][key] = {
            k: None if isinstance(v, float) and math.isnan(v) else v for k, v in result.items()
        }
    audit = Audit()
    result = replay_job(checks, raw, params, solve, audit)
    assert audit.ok(), audit.errors
    assert result["comparisons"]["base_independent"]["objective_max_residual"] == 0.0
    assert result["base"] == result["tighter"] == 1
    assert result["base_statuses"] == result["tighter_statuses"] == {"feasible": 1}
    assert result["evidence_kind"].startswith("shared-pinned-oracle-reproduction")


@pytest.mark.parametrize(
    "status,bad_mask",
    [("feasible", True), ("feasible", 1 - RATE / 2), ("infeasible", RATE / 2), ("unresolved", 0.0)],
)
def test_status_requires_its_exact_indicator(status, bad_mask):
    record = oracle_fixture([1, 1, 4, 0, 0], 1 if status == "feasible" else None, status)
    record["feasible"] = bad_mask
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert not audit.ok()
    assert any(e["field"].startswith("oracle.feasible") for e in audit.errors)


def test_accepted_optional_final_rate_null_is_a_mask_failure():
    record = oracle_fixture([1, 1, 4, 0, 0], 1.0)
    record["gamma_ww"] = None
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert "oracle.gamma_ww.mask" in audit.counts


def test_unresolved_candidate_retains_attempted_rate_diagnostics():
    record = oracle_fixture([1, 1, 4, 0, 0], 0.25, "unresolved")
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert audit.ok(), audit.errors


def test_budget_guard_checks_after_a_completed_solver_call():
    checks, raw, params, solve = synthetic_replay()
    completed = False

    def completing_solver(*values, **policy):
        nonlocal completed
        result = solve(*values, **policy)
        completed = True
        return result

    def deadline():
        if completed:
            raise TimeoutError("deadline after solver completion")

    with pytest.raises(TimeoutError, match="deadline after solver completion"):
        replay_job(checks, raw, params, completing_solver, Audit(), budget_check=deadline)
