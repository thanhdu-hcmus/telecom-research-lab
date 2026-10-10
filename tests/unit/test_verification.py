import numpy as np
import pytest

from lab.io import LabError
from lab.simkit.wireless import noma_sinr, rates
from lab.verification import average_ci, independent_noma, outage_ci, paired_ci


def test_ci_zero_and_counts():
    zero = outage_ci(0, 1000)
    assert 0 < zero["zero_event_upper_bound"] < 0.005 and not zero["conclusive"]
    assert not outage_ci(1, 1000)["conclusive"]
    assert outage_ci(100, 10000)["conclusive"]
    ci = average_ci([1, 2, 3])
    assert ci["low"] < 2 < ci["high"]
    assert paired_ci([1, 2, 3], [0.5, 1.5, 2.5])["mean"] == 0.5
    with pytest.raises(LabError):
        average_ci([1])


def test_independent_metrics_match_fixed_inputs():
    gains = np.array([[0.1, 2], [1, 4], [2, 5]])
    params = dict(rho_linear=10, a_weak=0.8, target_rate_weak=1, target_rate_strong=1)
    actual = independent_noma(gains, params)
    weak, sic, strong = noma_sinr(gains[:, 0], gains[:, 1], 10)
    assert np.allclose(actual[:, 0], rates(weak) + rates(strong))
