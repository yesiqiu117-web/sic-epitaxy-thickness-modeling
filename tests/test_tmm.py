import numpy as np

from epitaxy.optics.tmm import single_layer_reflectance


def test_tmm_reflectance_is_finite_and_nonnegative():
    wn = np.linspace(800, 4000, 500)
    n1 = np.full_like(wn, 3.42 + 0.003j, dtype=complex)
    n2 = np.full_like(wn, 3.55 + 0.02j, dtype=complex)
    r = single_layer_reflectance(wn, 20.0, 10.0, n1, n2)
    assert np.all(np.isfinite(r))
    assert np.all(r >= 0)
