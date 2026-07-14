import numpy as np

from epitaxy.estimation.hilbert_phase import estimate_hilbert_thickness


def test_hilbert_recovers_thickness():
    x = np.linspace(3000, 10000, 5000)
    d_um = 14.0
    f0 = 2 * d_um * 1e-4
    y = np.cos(2 * np.pi * f0 * x + 0.2)
    result = estimate_hilbert_thickness(x, y, f0)
    assert abs(result.thickness_um - d_um) < 0.3
