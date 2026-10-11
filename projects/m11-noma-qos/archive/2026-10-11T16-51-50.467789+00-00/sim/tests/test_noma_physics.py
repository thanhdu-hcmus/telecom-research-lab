"""Deterministic P5 checks; no random experiments or unpublished expected gains."""

import importlib.util
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

SOURCE = Path(__file__).parents[1] / "src"


def load_module(name):
    spec = importlib.util.spec_from_file_location("m11_" + name, SOURCE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analytic = load_module("analytic")
oracle = load_module("oracle")


@pytest.mark.parametrize(
    "inputs,expected",
    [
        ((0, 1, 2, 0, 0), "feasible"),
        ((0, 1, 2, 1e-14, 0), "infeasible"),
        ((1, 0, 0, 0, 0), "feasible"),
        ((1, 0, 0, 0, 1), "infeasible"),
        ((1, 0, 3, 0, 1), "feasible"),
        ((1, 0, 3, 1e-14, 0), "infeasible"),
        ((1, 3, 6, 1, 1), "feasible"),
        ((1, 3, 9, 1, 2), "feasible"),
        ((1, 3, 3, 1, 1), "feasible"),
        ((1, 1, 2, 2, 2), "infeasible"),
        ((1, 3, 6, 0, 0), "feasible"),
        ((1, 3, 6, 2, 0), "feasible"),
    ],
)
def test_independent_feasibility_and_objective(inputs, expected):
    closed = analytic.solve(*inputs)
    separate = oracle.solve(*inputs)
    assert closed["status"].item() == expected
    assert separate["status"] == expected
    if expected == "feasible":
        assert math.isclose(closed["sum_rate"].item(), separate["sum_rate"], abs_tol=1e-7)
        assert closed["residual_w"] >= -1e-9
        assert closed["residual_s"] >= -1e-9
        assert separate["residual_w"] >= -1e-9
        assert separate["residual_s"] >= -1e-9
        assert closed["sic_residual"] >= -1e-9
        assert separate["sic_residual"] >= -1e-9
    else:
        assert math.isnan(closed["a_star"].item())
        assert math.isnan(closed["sum_rate"].item())
        assert math.isnan(separate["a_star"])
        assert math.isnan(separate["sum_rate"])


@pytest.mark.parametrize("gs,qw,qs", [(9, 1, 2), (3, 1, 1)])
def test_exact_singleton_with_nonrepresentable_split(gs, qw, qs):
    closed = analytic.solve(1, 3, gs, qw, qs)
    separate = oracle.solve(1, 3, gs, qw, qs)
    assert closed["singleton"].item()
    assert separate["singleton"]
    assert closed["exact_split"].item() == separate["exact_split"] == "1/3"
    assert closed["certificate"].item() == "exact-rational"
    assert separate["feasibility_certificate"] == "exact-rational"
    # The exact rational witness, rather than its binary64 approximation,
    # certifies both original SINR constraints.
    a = Fraction(separate["exact_split"])
    assert (1 - a) * 3 / (1 + a * 3) >= 2**qw - 1
    assert a * gs >= 2**qs - 1


def test_brief_example_is_not_singleton():
    solved = analytic.solve(1, 3, 6, 1, 1)
    assert not solved["singleton"].item()
    assert math.isclose(solved["interval_lower"].item(), 1 / 6)
    assert math.isclose(solved["interval_upper"].item(), 1 / 3)


def test_broadcast_and_unfiltered_oma_rates():
    solved = analytic.solve(np.array([[0], [1]]), [1, 3], [2, 6], 0, 0)
    assert solved["sum_rate"].shape == (2, 2)
    np.testing.assert_allclose(
        solved["oma_rw"], np.log1p(np.array([[0, 0], [1, 3]])) / (2 * math.log(2))
    )
    assert np.all(solved["category"] == "n11")
    np.testing.assert_allclose(solved["a_star"], 1)


def test_original_sinrs_and_half_block_reference():
    rates = analytic.direct_rates(2, 3, 9, 0.25)
    other = oracle.direct_rates(2, 3, 9, 0.25)
    assert rates["gamma_ww"].item() == pytest.approx(0.75 * 6 / (1 + 0.25 * 6))
    assert rates["gamma_ws"].item() == pytest.approx(0.75 * 18 / (1 + 0.25 * 18))
    assert rates["gamma_ss"].item() == pytest.approx(0.25 * 18)
    for name in rates:
        assert rates[name].item() == pytest.approx(other[name], abs=1e-12)
    solved = analytic.solve(2, 3, 9, 0, 0)
    assert solved["oma_rw"].item() == pytest.approx(0.5 * math.log2(7))
    assert solved["oma_rs"].item() == pytest.approx(0.5 * math.log2(19))


def test_equal_gains_tie_and_zero_branch():
    solved = analytic.solve(1, 3, 3, 0, 0)
    assert not solved["optimizer_unique"].item()
    assert solved["sum_rate"].item() == pytest.approx(2)
    assert solved["paired_difference"].item() == pytest.approx(0)
    zero = analytic.solve(0, 1, 2, 0, 0)
    assert zero["a_star"].item() == 1
    assert zero["sum_rate"].item() == 0
    assert not zero["optimizer_unique"].item()


def test_noninteger_near_singleton_is_unresolved_not_relaxed():
    a, A, B = 0.25, 3.0, 6.0
    qw = math.log2((1 + A) / (1 + a * A))
    qs = math.log2(1 + a * B)
    solved = analytic.solve(1, A, B, qw, qs)
    separate = oracle.solve(1, A, B, qw, qs)
    assert solved["status"].item() == "unresolved"
    assert solved["boundary_flag"].item()
    assert math.isnan(solved["feasible"].item())
    assert math.isnan(solved["sum_rate"].item())
    assert separate["status"] == "unresolved"


def test_caps_and_product_domain_fail_closed():
    assert oracle.solve(1, 3, 9, 0.5, 0.5, max_root_iterations=1)["status"] == "unresolved"
    for inputs in ((1e308, 2, 3, 0, 0), (1e-300, 1e-300, 2e-300, 0, 0)):
        assert analytic.solve(*inputs)["status"].item() == "unresolved"
        assert oracle.solve(*inputs)["status"] == "unresolved"


@pytest.mark.parametrize(
    "inputs",
    [
        (-1, 1, 2, 0, 0),
        (1, 2, 1, 0, 0),
        (1, 1, 2, -1, 0),
        (math.inf, 1, 2, 0, 0),
        (1, 1, 2, math.nan, 0),
    ],
)
def test_invalid_domain_rejected(inputs):
    with pytest.raises(ValueError):
        analytic.solve(*inputs)
    with pytest.raises(ValueError):
        oracle.solve(*inputs)


def test_oma_exact_boundary_and_no_zero_substitution():
    solved = analytic.solve(1, 3, 3, 1, 1)
    assert solved["oma_status"].item() == "feasible"
    assert solved["oma_certificate"].item() == "exact-rational"
    impossible = analytic.solve(1, 1, 2, 4, 4)
    assert impossible["category"].item() == "n00"
    assert impossible["oma_sum"].item() > 0  # labeled unconstrained reference
    assert math.isnan(impossible["paired_difference"].item())
    assert math.isnan(impossible["sum_rate"].item())
