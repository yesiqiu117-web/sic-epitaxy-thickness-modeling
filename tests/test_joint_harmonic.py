import numpy as np

from epitaxy.estimation.joint_harmonic import fit_joint_harmonic
from epitaxy.types import ProcessedSpectrum, Spectrum


def _processed(name: str, angle: float, d_um: float):
    wn = np.linspace(1200.0, 4000.0, 2400)
    n = np.full_like(wn, 2.55)
    x = wn * np.sqrt(n**2 - np.sin(np.deg2rad(angle)) ** 2)
    phi = 4 * np.pi * d_um * 1e-4 * x
    y = np.cos(phi) + 0.18 * np.cos(3 * phi + 0.3)
    raw = Spectrum(name, angle, wn, y)
    return ProcessedSpectrum(raw, wn, y, y, np.zeros_like(y), y,
                             np.ones_like(y), y, np.zeros_like(y, dtype=bool))


def test_joint_harmonic_recovers_fundamental():
    spectra = [_processed("a", 10.0, 8.0), _processed("b", 15.0, 8.0)]
    n_fn = lambda wn: np.full_like(np.asarray(wn, dtype=float), 2.55)
    result = fit_joint_harmonic(spectra, [n_fn, n_fn], 7.9, (6.0, 10.0), 3)
    assert result.success
    assert abs(result.thickness_um - 8.0) < 0.02
    assert result.metrics["rmse"] < 1e-5
