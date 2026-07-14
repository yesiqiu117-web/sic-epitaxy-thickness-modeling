import numpy as np

from epitaxy.estimation.peak_regression import estimate_peak_regression


def test_peak_regression_recovers_thickness():
    x = np.linspace(3000, 10000, 8000)
    d_um = 11.0
    y = np.cos(4 * np.pi * d_um * 1e-4 * x)
    result = estimate_peak_regression(x, y, kind="peak", prominence=0.5, distance=100)
    assert abs(result.thickness_um - d_um) < 0.2
