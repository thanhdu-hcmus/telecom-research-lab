from pathlib import Path

import cvxpy as cp
import numpy as np
from scipy.stats import binomtest

from lab.io import load
from lab.simkit import wireless as w


def contains(events, n, p):
    ci = binomtest(int(events), n).proportion_ci(confidence_level=0.999, method="exact")
    assert ci.low <= p <= ci.high


def test_units_streams_channels():
    assert np.isclose(w.dbm_to_watt(30), 1)
    assert np.isclose(w.watt_to_dbm(0.001), 0)
    assert np.isclose(w.noise_watt(1), w.dbm_to_watt(-174))
    a = w.streams(8)
    b = w.streams(8)
    assert np.array_equal(w.rayleigh(a["channel"], 100), w.rayleigh(b["channel"], 100))
    h = w.rayleigh(np.random.default_rng(8), 300000)
    assert abs(np.mean(abs(h) ** 2) - 1) < 0.01
    assert np.isclose(w.path_gain(10, 2), 0.01)


def test_bpsk_rayleigh_outage_capacity():
    n = 400000
    rng = np.random.default_rng(312)
    noise = rng.standard_normal(n)
    gain = abs(w.rayleigh(rng, n)) ** 2
    for rho in [1, 2, 4]:
        contains(np.sum(1 + noise / np.sqrt(2 * rho) < 0), n, w.bpsk_ber(rho))
        contains(np.sum(gain * rho < 1), n, w.rayleigh_outage(rho))
        values = w.rates(gain * rho)
        assert abs(values.mean() - w.rayleigh_capacity(rho)) < 4 * values.std(ddof=1) / np.sqrt(n)


def test_ris_aperture_scaling():
    rng = np.random.default_rng(5)
    powers = []
    sizes = [64, 128, 256, 512]
    for n in sizes:
        g = w.rayleigh(rng, (4000, n))
        h = w.rayleigh(rng, (4000, n))
        powers.append(np.mean(abs(w.ris_cascade(g, h)) ** 2))
    slope = np.polyfit(np.log(sizes), np.log(powers), 1)[0]
    assert 1.9 <= slope <= 2.1


def test_ordered_noma_outage():
    n = 400000
    rng = np.random.default_rng(93)
    gains = np.sort(rng.exponential(size=(n, 2)), axis=1)
    reference = load(
        Path(__file__).resolve().parents[2] / "tests/fixtures/modeler-derived-outage.yaml"
    )
    for sample in reference["samples"]:
        if sample["a_weak"] != 0.8:
            continue
        rho = sample["rho"]
        weak, sic, strong = w.noma_sinr(gains[:, 0], gains[:, 1], rho)
        pw, ps = w.noma_outage_closed(rho, 0.8, 1, 1)
        assert np.allclose([pw, ps], [sample["p_weak"], sample["p_strong"]], rtol=1e-10, atol=1e-12)
        contains(np.sum(weak < 1), n, pw)
        contains(np.sum((sic < 1) | (strong < 1)), n, ps)
    assert w.noma_outage_closed(10, 0.2, 1, 1) == (1, 1)


def test_waterfill_vs_cvxpy():
    gains = np.array([0.5, 1, 3, 5])
    power = 2
    analytic = w.waterfill(gains, power)
    p = cp.Variable(4, nonneg=True)
    problem = cp.Problem(cp.Maximize(cp.sum(cp.log1p(cp.multiply(gains, p)))), [cp.sum(p) <= power])
    assert problem.is_dcp()
    problem.solve(solver="CLARABEL")
    assert problem.status == "optimal"
    assert np.allclose(p.value, analytic, atol=0.0002)
