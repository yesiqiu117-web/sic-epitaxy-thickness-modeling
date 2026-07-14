import numpy as np

from epitaxy.estimation.fft_init import estimate_fft_thickness


def test_fft_recovers_thickness():
    x = np.linspace(3000, 10000, 4000)
    d_um = 15.0
    y = np.cos(4 * np.pi * d_um * 1e-4 * x)
    result = estimate_fft_thickness(x, y, thickness_bounds_um=(5, 30))
    assert abs(result.thickness_um - d_um) < 0.5
