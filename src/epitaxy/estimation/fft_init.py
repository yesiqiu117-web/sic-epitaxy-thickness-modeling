from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks, windows

from .common import uniform_resample


@dataclass
class FFTThicknessResult:
    thickness_um: float
    fundamental_frequency: float
    frequencies: np.ndarray
    amplitudes: np.ndarray
    candidates_um: list[float]


def estimate_fft_thickness(
    x: np.ndarray,
    y: np.ndarray,
    thickness_bounds_um=(1.0, 1000.0),
    min_cycles: float = 2.0,
) -> FFTThicknessResult:
    xu, yu = uniform_resample(x, y)
    yu = yu - np.mean(yu)
    win = windows.hann(len(yu), sym=False)
    dx = float(np.median(np.diff(xu)))
    freq = np.fft.rfftfreq(len(yu), d=dx)
    amp = np.abs(np.fft.rfft(yu * win))
    lo_um, hi_um = map(float, thickness_bounds_um)
    f_lo = max(2.0 * lo_um * 1e-4, min_cycles / max(np.ptp(xu), 1e-12))
    f_hi = min(2.0 * hi_um * 1e-4, freq.max())
    valid = (freq >= f_lo) & (freq <= f_hi)
    if not np.any(valid):
        raise ValueError("FFT 搜索范围为空，请检查厚度边界和采样间隔。")
    local_freq = freq[valid]
    local_amp = amp[valid]
    peaks, _ = find_peaks(local_amp, prominence=0.02 * max(local_amp.max(), 1e-12))
    if len(peaks) == 0:
        idx = int(np.argmax(local_amp))
        candidate_indices = [idx]
    else:
        order = peaks[np.argsort(local_amp[peaks])[::-1]]
        candidate_indices = order[:8].tolist()
    best_idx = candidate_indices[0]
    f0 = float(local_freq[best_idx])
    d_um = f0 * 0.5 * 1e4
    candidates = [float(local_freq[i] * 0.5 * 1e4) for i in candidate_indices]
    return FFTThicknessResult(d_um, f0, freq, amp, candidates)
