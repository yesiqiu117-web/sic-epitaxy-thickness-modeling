from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FinalThicknessEstimate:
    estimator: str
    thickness_um: float
    values_um: list[float]
    per_angle_um: dict[str, float]
    cross_angle_relative_pct: float
    uncorrected_consensus_um: float


def _finite_values(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    values = frame[columns].to_numpy(dtype=float).ravel()
    return values[np.isfinite(values)]


def estimate_final_thickness(
    single_methods: pd.DataFrame,
    estimator: str,
) -> FinalThicknessEstimate:
    """Select the paper-facing thickness estimator explicitly.

    ``fundamental_consensus`` uses peak, valley and Hilbert estimates after
    fundamental-band isolation.  It is appropriate when repeated reflections do
    not materially move the extrema.

    ``peak_only`` uses only peak coordinates.  In an Airy/multi-beam pattern the
    peak locations retain the fundamental optical period more reliably than the
    valleys, so this is used as the correction estimator for the silicon data.
    """
    estimator = str(estimator).lower()
    if estimator == "fundamental_consensus":
        columns = ["peak_um", "valley_um", "hilbert_um"]
    elif estimator == "peak_only":
        columns = ["peak_um"]
    elif estimator == "all_methods_median":
        columns = ["fft_um", "peak_um", "valley_um", "hilbert_um"]
    else:
        raise ValueError(f"未知最终估计器：{estimator}")

    values = _finite_values(single_methods, columns)
    if values.size == 0:
        raise ValueError("最终厚度估计没有可用结果。")

    per_angle: dict[str, float] = {}
    for _, row in single_methods.iterrows():
        local = np.asarray([row[c] for c in columns], dtype=float)
        local = local[np.isfinite(local)]
        if local.size:
            per_angle[str(row["dataset"])] = float(np.median(local))

    angle_values = np.asarray(list(per_angle.values()), dtype=float)
    if len(angle_values) >= 2:
        cross_angle = float(
            (np.max(angle_values) - np.min(angle_values))
            / max(np.mean(angle_values), 1e-12)
            * 100.0
        )
    else:
        cross_angle = float("nan")

    all_values = _finite_values(
        single_methods, ["fft_um", "peak_um", "valley_um", "hilbert_um"]
    )
    return FinalThicknessEstimate(
        estimator=estimator,
        thickness_um=float(np.median(values)),
        values_um=[float(v) for v in values],
        per_angle_um=per_angle,
        cross_angle_relative_pct=cross_angle,
        uncorrected_consensus_um=float(np.median(all_values)),
    )
