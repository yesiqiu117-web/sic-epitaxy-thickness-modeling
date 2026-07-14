from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter

from .types import ProcessedSpectrum, Spectrum


def _valid_odd_window(requested: int, n: int, polyorder: int) -> int:
    window = min(int(requested), n if n % 2 == 1 else n - 1)
    window = max(window, polyorder + 2)
    if window % 2 == 0:
        window -= 1
    if window <= polyorder:
        window = polyorder + 1 + ((polyorder + 1) % 2 == 0)
    return min(window, n if n % 2 == 1 else n - 1)


def hampel_filter(y: np.ndarray, window: int = 7, n_sigma: float = 3.5):
    y = np.asarray(y, dtype=float)
    n = len(y)
    corrected = y.copy()
    mask = np.zeros(n, dtype=bool)
    k = max(1, int(window))
    for i in range(n):
        lo, hi = max(0, i - k), min(n, i + k + 1)
        local = y[lo:hi]
        med = np.median(local)
        mad = np.median(np.abs(local - med))
        scale = 1.4826 * mad
        if scale > 0 and abs(y[i] - med) > n_sigma * scale:
            corrected[i] = med
            mask[i] = True
    return corrected, mask


def robust_polynomial_baseline(
    x: np.ndarray,
    y: np.ndarray,
    degree: int = 3,
    iterations: int = 6,
) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = (x - x.mean()) / max(np.ptp(x), 1.0)
    weights = np.ones_like(y)
    coeff = np.polyfit(z, y, degree, w=weights)
    for _ in range(max(1, iterations)):
        baseline = np.polyval(coeff, z)
        resid = y - baseline
        med = np.median(resid)
        mad = 1.4826 * np.median(np.abs(resid - med)) + 1e-12
        u = (resid - med) / (4.685 * mad)
        weights = (1 - u**2) ** 2
        weights[np.abs(u) >= 1] = 0.02
        coeff = np.polyfit(z, y, degree, w=np.sqrt(weights + 1e-8))
    return np.polyval(coeff, z)


def preprocess_spectrum(spectrum: Spectrum, cfg: dict) -> ProcessedSpectrum:
    wn = spectrum.wavenumber_cm1
    r = spectrum.reflectance
    cleaned, outlier_mask = hampel_filter(
        r,
        window=cfg.get("hampel_window", 7),
        n_sigma=cfg.get("hampel_sigma", 3.5),
    )
    sg_window = _valid_odd_window(
        cfg.get("sg_window", 21), len(cleaned), cfg.get("sg_polyorder", 3)
    )
    smoothed = savgol_filter(cleaned, sg_window, cfg.get("sg_polyorder", 3))
    baseline = robust_polynomial_baseline(
        wn,
        smoothed,
        degree=cfg.get("baseline_degree", 3),
        iterations=cfg.get("baseline_iterations", 6),
    )
    residual = smoothed - baseline
    env_window = _valid_odd_window(
        cfg.get("envelope_window", 301), len(residual), cfg.get("envelope_polyorder", 2)
    )
    envelope = savgol_filter(
        np.abs(residual), env_window, cfg.get("envelope_polyorder", 2)
    )
    floor = cfg.get("min_envelope_fraction", 0.08) * max(
        np.percentile(np.abs(residual), 90), 1e-12
    )
    envelope = np.maximum(envelope, floor)
    normalized = residual / envelope
    med = np.median(normalized)
    scale = 1.4826 * np.median(np.abs(normalized - med))
    if scale > 0:
        normalized = (normalized - med) / scale
    return ProcessedSpectrum(
        raw=spectrum,
        wavenumber_cm1=wn,
        reflectance=r,
        smoothed=smoothed,
        baseline=baseline,
        residual=residual,
        envelope=envelope,
        normalized=normalized,
        outlier_mask=outlier_mask,
    )
