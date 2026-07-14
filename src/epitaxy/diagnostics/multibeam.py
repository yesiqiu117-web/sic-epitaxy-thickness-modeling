from __future__ import annotations

import numpy as np
import pandas as pd

from ..types import FitResult, ProcessedSpectrum


def _relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max((abs(a) + abs(b)) / 2.0, 1e-12) * 100.0


def assess_multibeam_effect(
    single_methods: pd.DataFrame,
    processed: list[ProcessedSpectrum],
    two_beam: FitResult,
    harmonic3: FitResult,
    thresholds: dict | None = None,
) -> dict:
    """Combine physically complementary evidence for multi-beam influence.

    A lower BIC for a harmonic model only proves that the waveform is not a pure
    sinusoid.  To avoid false positives from baseline drift or weak dispersion
    mismatch, the final classification additionally requires a peak/valley
    thickness split, a visible second harmonic, and sufficiently high fringe
    visibility.
    """
    thresholds = thresholds or {}
    pv_threshold = float(thresholds.get("peak_valley_pct", 1.0))
    h2_threshold = float(thresholds.get("h2_h1", 0.04))
    visibility_threshold = float(thresholds.get("visibility", 0.12))
    bic_threshold = float(thresholds.get("delta_bic", 10.0))

    per_dataset = []
    for _, row in single_methods.iterrows():
        peak = float(row["peak_um"])
        valley = float(row["valley_um"])
        per_dataset.append(
            {
                "dataset": str(row["dataset"]),
                "peak_valley_relative_pct": _relative_difference(peak, valley),
                "h2_h1": float(row["h2_h1"]),
                "h3_h1": float(row["h3_h1"]),
            }
        )

    visibilities = []
    for spec in processed:
        p95 = float(np.percentile(spec.smoothed, 95))
        p05 = float(np.percentile(spec.smoothed, 5))
        visibility = (p95 - p05) / max(abs(p95 + p05), 1e-12)
        visibilities.append(float(visibility))

    pv_median = float(np.median([r["peak_valley_relative_pct"] for r in per_dataset]))
    h2_median = float(np.median([r["h2_h1"] for r in per_dataset]))
    visibility_median = float(np.median(visibilities))
    delta_bic = float(two_beam.metrics["bic"] - harmonic3.metrics["bic"])
    non_sinusoidal = bool(delta_bic > bic_threshold)
    materially_significant = bool(
        pv_median > pv_threshold
        and h2_median > h2_threshold
        and visibility_median > visibility_threshold
    )

    if materially_significant:
        classification = "significant_multi_beam"
        conclusion = (
            "多项证据同时超过阈值，多光束干涉会使波谷/全波形双光束估计产生系统偏差；"
            "最终厚度采用基频隔离后的峰坐标估计。"
        )
    elif non_sinusoidal:
        classification = "non_sinusoidal_but_not_material"
        conclusion = (
            "高阶谐波模型能改善拟合，但峰谷厚度一致、二次谐波和条纹可见度较低；"
            "现有证据不足以认定多光束对厚度造成实质影响。"
        )
    else:
        classification = "double_beam_adequate"
        conclusion = "双光束模型对当前厚度计算已足够。"

    return {
        "classification": classification,
        "materially_significant": materially_significant,
        "non_sinusoidal_waveform": non_sinusoidal,
        "peak_valley_median_relative_pct": pv_median,
        "median_h2_h1": h2_median,
        "median_h3_h1": float(np.median([r["h3_h1"] for r in per_dataset])),
        "median_fringe_visibility": visibility_median,
        "delta_bic_two_minus_harmonic3": delta_bic,
        "thresholds": {
            "peak_valley_pct": pv_threshold,
            "h2_h1": h2_threshold,
            "visibility": visibility_threshold,
            "delta_bic": bic_threshold,
        },
        "per_dataset": per_dataset,
        "conclusion": conclusion,
    }
