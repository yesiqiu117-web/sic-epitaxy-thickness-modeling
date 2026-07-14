from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import hilbert

from .common import robust_linear_fit, uniform_resample


@dataclass
class HilbertThicknessResult:
    thickness_um: float
    slope: float
    r2: float
    x_uniform: np.ndarray
    filtered_signal: np.ndarray
    phase: np.ndarray
    phase_fit: np.ndarray


def estimate_hilbert_thickness(
    x: np.ndarray,
    y: np.ndarray,
    fundamental_frequency: float,
    band_ratio=(0.55, 1.45),
) -> HilbertThicknessResult:
    xu, yu = uniform_resample(x, y)
    yu = yu - np.mean(yu)
    dx = np.median(np.diff(xu))
    freq = np.fft.rfftfreq(len(yu), d=dx)
    spectrum = np.fft.rfft(yu)
    lo, hi = fundamental_frequency * band_ratio[0], fundamental_frequency * band_ratio[1]
    mask = (freq >= lo) & (freq <= hi)
    if mask.sum() < 2:
        raise ValueError("Hilbert 带通范围内频点过少。")
    filtered_spec = np.zeros_like(spectrum)
    filtered_spec[mask] = spectrum[mask]
    filtered = np.fft.irfft(filtered_spec, n=len(yu))
    analytic = hilbert(filtered)
    amplitude = np.abs(analytic)
    phase = np.unwrap(np.angle(analytic))
    valid = amplitude > np.percentile(amplitude, 20)
    edge = max(3, int(0.05 * len(xu)))
    valid[:edge] = False
    valid[-edge:] = False
    slope, intercept, r2, pred_valid = robust_linear_fit(xu[valid], phase[valid])
    phase_fit = slope * xu + intercept
    thickness_um = abs(slope) / (4.0 * np.pi) * 1e4
    return HilbertThicknessResult(
        thickness_um=float(thickness_um),
        slope=float(slope),
        r2=float(r2),
        x_uniform=xu,
        filtered_signal=filtered,
        phase=phase,
        phase_fit=phase_fit,
    )
