import math

import numpy as np
from scipy.special import exp1, ndtr

from lab.io import LabError


def db_to_linear(db):
    return np.power(10.0, np.asarray(db) / 10)


def linear_to_db(value):
    x = np.asarray(value)
    if np.any(x <= 0):
        raise LabError("dB conversion requires positive values")
    return 10 * np.log10(x)


def dbm_to_watt(dbm):
    return db_to_linear(np.asarray(dbm) - 30)


def watt_to_dbm(w):
    return linear_to_db(w) + 30


def noise_watt(bandwidth_hz, nf_db=0):
    if bandwidth_hz <= 0:
        raise LabError("Bandwidth must be positive")
    return dbm_to_watt(-174 + 10 * np.log10(bandwidth_hz) + nf_db)


def streams(seed):
    return dict(
        zip(
            ["channel", "noise", "initialization"],
            [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(3)],
        )
    )


def rayleigh(rng, shape):
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2)


def rician(rng, shape, k_linear, los=1):
    if k_linear < 0:
        raise LabError("Rician K must be nonnegative linear ratio")
    return np.sqrt(k_linear / (k_linear + 1)) * np.broadcast_to(los, shape) + np.sqrt(
        1 / (k_linear + 1)
    ) * rayleigh(rng, shape)


def path_gain(distance, exponent, reference_distance=1, reference_gain=1):
    if np.any(np.asarray(distance) < reference_distance) or exponent <= 0 or reference_gain <= 0:
        raise LabError("Distance/model parameters outside declared regime")
    return reference_gain * (np.asarray(distance) / reference_distance) ** (-exponent)


def ris_cascade(g, h, phase=None):
    product = np.asarray(g) * np.asarray(h)
    if phase is None:
        phase = np.exp(-1j * np.angle(product))
    if not np.allclose(np.abs(phase), 1):
        raise LabError("Passive ideal RIS phase must be unit modulus")
    return np.sum(product * phase, axis=-1)


def rates(sinr):
    if np.any(np.asarray(sinr) < 0):
        raise LabError("SINR must be nonnegative")
    return np.log2(1 + np.asarray(sinr))


def noma_sinr(gain_weak, gain_strong, rho, a_weak=0.8, residual=0):
    if not 0 < a_weak < 1 or not 0 <= residual <= 1 or rho <= 0:
        raise LabError("Invalid NOMA allocation/SIC/SNR")
    a_strong = 1 - a_weak
    g1, g2 = np.asarray(gain_weak), np.asarray(gain_strong)
    return (
        a_weak * rho * g1 / (a_strong * rho * g1 + 1),
        a_weak * rho * g2 / (a_strong * rho * g2 + 1),
        a_strong * rho * g2 / (residual * a_weak * rho * g2 + 1),
    )


def noma_outage_closed(rho, a_weak, rate_weak, rate_strong):
    """Two ORDERED iid unit-mean exponential gains, perfect SIC, fixed power.

    Weak=min(X,Y), strong=max(X,Y). No random-location path-loss averaging.
    SIC feasibility a_weak>gamma_weak*a_strong; infeasible means outage one.
    """
    a_strong = 1 - a_weak
    gw = 2**rate_weak - 1
    gs = 2**rate_strong - 1
    if rho <= 0 or not 0 < a_weak < 1 or min(rate_weak, rate_strong) < 0:
        raise LabError("Invalid NOMA outage parameters")
    if a_weak <= gw * a_strong:
        return 1.0, 1.0
    tw = gw / (rho * (a_weak - gw * a_strong))
    ts = max(tw, gs / (rho * a_strong))
    return float(-np.expm1(-2 * tw)), float((-np.expm1(-ts)) ** 2)


def bpsk_ber(rho):
    return ndtr(-np.sqrt(2 * np.asarray(rho)))


def rayleigh_outage(rho, threshold=1):
    return -np.expm1(-threshold / np.asarray(rho))


def rayleigh_capacity(rho):
    x = 1 / np.asarray(rho, dtype=float)
    if np.any(x <= 0):
        raise LabError("SNR must be positive")
    # Asymptotic E1 expansion avoids exp(x) overflow at low SNR.
    if np.ndim(x) == 0:
        return float(
            (
                np.exp(x) * exp1(x)
                if x < 500
                else sum((-1) ** k * math.factorial(k) / x ** (k + 1) for k in range(8))
            )
            / np.log(2)
        )
    return np.array([rayleigh_capacity(v) for v in np.asarray(rho)])


def waterfill(gains, power):
    g = np.asarray(gains, dtype=float)
    if np.any(g <= 0) or power < 0:
        raise LabError("Positive gains and nonnegative total power required")
    lo, hi = 0, float(power + max(1 / g))
    for _ in range(100):
        level = (lo + hi) / 2
        if np.maximum(level - 1 / g, 0).sum() > power:
            hi = level
        else:
            lo = level
    return np.maximum((lo + hi) / 2 - 1 / g, 0)
