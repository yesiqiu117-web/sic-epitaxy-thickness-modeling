from __future__ import annotations

import numpy as np
import pandas as pd

from ..estimation.common import uniform_resample
from ..estimation.fft_init import estimate_fft_thickness
from ..estimation.hilbert_phase import estimate_hilbert_thickness
from ..estimation.peak_regression import (
    _fundamental_reconstruction,
    estimate_peak_regression,
)
from ..optics.refractive_index import corrected_wavenumber
from ..types import ProcessedSpectrum


def block_bootstrap_indices(n: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0:
        return np.array([], dtype=int)
    block_size = max(1, min(int(block_size), n))
    starts = np.arange(0, n - block_size + 1)
    chunks = []
    total = 0
    while total < n:
        start = int(rng.choice(starts))
        chunk = np.arange(start, start + block_size)
        chunks.append(chunk)
        total += len(chunk)
    return np.concatenate(chunks)[:n]


def percentile_interval(values, confidence_level: float = 0.95):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan")
    alpha = 1.0 - confidence_level
    return (
        float(np.quantile(values, alpha / 2)),
        float(np.quantile(values, 1 - alpha / 2)),
    )


def bootstrap_final_thickness(
    processed: list[ProcessedSpectrum],
    layer_function,
    thickness_bounds_um: tuple[float, float],
    estimator: str,
    repeats: int = 400,
    block_size: int = 80,
    confidence_level: float = 0.95,
    random_seed: int = 2025,
    hilbert_band_ratio=(0.55, 1.45),
) -> tuple[pd.DataFrame, dict]:
    """Residual block bootstrap in the corrected-wavenumber domain.

    The fundamental-band reconstruction is kept fixed and contiguous blocks of
    the remaining residual are resampled.  This preserves local spectral
    correlation and avoids the invalid independent-point bootstrap.
    """
    estimator = str(estimator).lower()
    prepared = []
    for spec in processed:
        n = layer_function(spec.wavenumber_cm1)
        x = corrected_wavenumber(spec.wavenumber_cm1, n, spec.raw.angle_deg)
        xu, yu = uniform_resample(x, spec.normalized)
        fft = estimate_fft_thickness(xu, yu, thickness_bounds_um=thickness_bounds_um)
        _, fundamental = _fundamental_reconstruction(
            xu, yu, fft.fundamental_frequency, tuple(hilbert_band_ratio)
        )
        prepared.append(
            {
                "name": spec.raw.name,
                "x": xu,
                "fundamental": fundamental,
                "residual": yu - fundamental,
                "f0": float(fft.fundamental_frequency),
            }
        )

    rng = np.random.default_rng(int(random_seed))
    rows = []
    for repeat in range(int(repeats)):
        values = []
        failure = None
        for item in prepared:
            idx = block_bootstrap_indices(len(item["x"]), block_size, rng)
            y_boot = item["fundamental"] + item["residual"][idx]
            try:
                peak = estimate_peak_regression(
                    item["x"], y_boot, kind="peak",
                    fundamental_frequency=item["f0"],
                ).thickness_um
                if estimator == "peak_only":
                    values.append(float(peak))
                elif estimator == "fundamental_consensus":
                    valley = estimate_peak_regression(
                        item["x"], y_boot, kind="valley",
                        fundamental_frequency=item["f0"],
                    ).thickness_um
                    hilbert = estimate_hilbert_thickness(
                        item["x"], y_boot, item["f0"],
                        band_ratio=tuple(hilbert_band_ratio),
                    ).thickness_um
                    values.extend([float(peak), float(valley), float(hilbert)])
                else:
                    raise ValueError(f"bootstrap 不支持估计器：{estimator}")
            except (ValueError, RuntimeError) as exc:
                failure = str(exc)
                break
        rows.append(
            {
                "repeat": repeat,
                "thickness_um": float(np.median(values)) if values and failure is None else np.nan,
                "success": failure is None,
                "error": failure,
            }
        )

    frame = pd.DataFrame(rows)
    valid = frame.loc[frame["success"], "thickness_um"].to_numpy(dtype=float)
    ci_low, ci_high = percentile_interval(valid, confidence_level)
    summary = {
        "method": "fundamental_residual_block_bootstrap",
        "estimator": estimator,
        "repeats_requested": int(repeats),
        "repeats_successful": int(len(valid)),
        "block_size_points": int(block_size),
        "confidence_level": float(confidence_level),
        "mean_um": float(np.mean(valid)) if len(valid) else float("nan"),
        "median_um": float(np.median(valid)) if len(valid) else float("nan"),
        "standard_error_um": float(np.std(valid, ddof=1)) if len(valid) > 1 else float("nan"),
        "ci_low_um": ci_low,
        "ci_high_um": ci_high,
    }
    return frame, summary
