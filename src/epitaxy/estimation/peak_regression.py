from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks

from .common import robust_linear_fit, uniform_resample


@dataclass
class PeakRegressionResult:
    thickness_um: float
    kind: str
    positions_x: np.ndarray
    orders: np.ndarray
    predicted_orders: np.ndarray
    r2: float
    n_extrema: int


def _orders_with_missing_peak_correction(x_positions: np.ndarray) -> np.ndarray:
    if len(x_positions) < 2:
        return np.arange(len(x_positions), dtype=float)
    gaps = np.diff(x_positions)
    typical = np.median(gaps)
    increments = np.maximum(1, np.rint(gaps / max(typical, 1e-12))).astype(int)
    return np.concatenate([[0], np.cumsum(increments)]).astype(float)


def _fundamental_reconstruction(
    x: np.ndarray,
    y: np.ndarray,
    f0: float,
    band_ratio: tuple[float, float] = (0.62, 1.38),
):
    xu, yu = uniform_resample(x, y)
    yu = yu - np.mean(yu)
    dx = float(np.median(np.diff(xu)))
    freq = np.fft.rfftfreq(len(xu), d=dx)
    spectrum = np.fft.rfft(yu)
    mask = (freq >= band_ratio[0] * f0) & (freq <= band_ratio[1] * f0)
    filtered = np.zeros_like(spectrum)
    filtered[mask] = spectrum[mask]
    reconstructed = np.fft.irfft(filtered, n=len(xu))
    return xu, reconstructed


def estimate_peak_regression(
    x: np.ndarray,
    normalized: np.ndarray,
    kind: str = "peak",
    prominence: float = 0.25,
    distance: int = 8,
    fundamental_frequency: float | None = None,
) -> PeakRegressionResult:
    x_arr = np.asarray(x, dtype=float)
    signal = np.asarray(normalized, dtype=float)

    if fundamental_frequency is not None and fundamental_frequency > 0:
        x_arr, signal = _fundamental_reconstruction(
            x_arr, signal, float(fundamental_frequency)
        )
        dx = float(np.median(np.diff(x_arr)))
        period_samples = 1.0 / max(float(fundamental_frequency) * dx, 1e-12)
        distance = max(int(distance), int(0.55 * period_samples))
        # Reconstruction has a more homogeneous amplitude, so a relative
        # prominence is more reliable than a fixed raw-signal threshold.
        prominence = max(0.08 * float(np.ptp(signal)), 1e-8)

    if kind == "peak":
        idx, _ = find_peaks(signal, prominence=prominence, distance=distance)
    elif kind == "valley":
        idx, _ = find_peaks(-signal, prominence=prominence, distance=distance)
    else:
        raise ValueError("kind 必须为 peak 或 valley。")
    if len(idx) < 3:
        raise ValueError(f"检测到的{kind}少于 3 个，无法可靠回归。")

    positions = x_arr[idx]
    orders = _orders_with_missing_peak_correction(positions)
    slope, intercept, r2, pred = robust_linear_fit(positions, orders)
    thickness_um = abs(slope) * 0.5 * 1e4
    return PeakRegressionResult(
        thickness_um=float(thickness_um),
        kind=kind,
        positions_x=positions,
        orders=orders,
        predicted_orders=pred,
        r2=float(r2),
        n_extrema=int(len(idx)),
    )
