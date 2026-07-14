from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

from ..estimation.common import uniform_resample


def _design(xu: np.ndarray, frequency: float, max_harmonic: int):
    t = 2 * (xu - xu.min()) / max(np.ptp(xu), 1.0) - 1
    columns = [np.ones_like(xu), t, t**2]
    labels = ["const", "trend1", "trend2"]
    for k in range(1, max_harmonic + 1):
        columns.extend([
            np.cos(2 * np.pi * k * frequency * xu),
            np.sin(2 * np.pi * k * frequency * xu),
        ])
        labels.extend([f"cos{k}", f"sin{k}"])
    return np.column_stack(columns), labels


def harmonic_analysis(
    x: np.ndarray,
    y: np.ndarray,
    fundamental_frequency: float,
    max_harmonic: int = 4,
) -> pd.DataFrame:
    xu, yu = uniform_resample(x, y)
    yu = yu - np.mean(yu)

    # Refine the FFT-bin frequency locally.  Without this step, spectral leakage
    # can be misreported as a large third harmonic.
    f_init = float(fundamental_frequency)

    def rss_at(f):
        design, _ = _design(xu, float(f), max_harmonic)
        coef, *_ = np.linalg.lstsq(design, yu, rcond=None)
        resid = yu - design @ coef
        return float(np.sum(resid**2))

    refined = minimize_scalar(
        rss_at,
        bounds=(0.92 * f_init, 1.08 * f_init),
        method="bounded",
        options={"xatol": max(f_init * 1e-9, 1e-14)},
    )
    f0 = float(refined.x)
    design, labels = _design(xu, f0, max_harmonic)
    coef, *_ = np.linalg.lstsq(design, yu, rcond=None)

    amplitudes = []
    for k in range(1, max_harmonic + 1):
        c = coef[labels.index(f"cos{k}")]
        s = coef[labels.index(f"sin{k}")]
        amplitudes.append(float(np.hypot(c, s)))
    fundamental_amp = max(amplitudes[0], 1e-30)

    rows = []
    for k, amplitude in enumerate(amplitudes, start=1):
        rows.append({
            "harmonic": k,
            "frequency": k * f0,
            "amplitude": amplitude,
            "ratio_to_fundamental": amplitude / fundamental_amp,
            "refined_fundamental_frequency": f0,
        })
    return pd.DataFrame(rows)
