import numpy as np

from epitaxy.optics.refractive_index import build_refractive_index, corrected_wavenumber


def test_constant_index_and_corrected_wavenumber():
    wn = np.array([1000.0, 2000.0])
    fn = build_refractive_index({"model": "constant", "n": 2.6, "kappa": 0.01})
    n = fn(wn)
    assert np.allclose(n.real, 2.6)
    x = corrected_wavenumber(wn, n, 10.0)
    assert np.all(np.diff(x) > 0)
