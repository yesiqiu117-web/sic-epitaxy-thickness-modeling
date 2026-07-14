from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..estimation.fft_init import estimate_fft_thickness
from ..estimation.hilbert_phase import estimate_hilbert_thickness
from ..estimation.peak_regression import estimate_peak_regression
from ..io import crop_spectrum, load_spectrum_excel
from ..optics.refractive_index import build_refractive_index, corrected_wavenumber
from ..preprocessing import preprocess_spectrum


def relative_change_percent(value: float, reference: float) -> float:
    return abs(value - reference) / abs(reference) * 100.0 if reference != 0 else float("nan")


def _resolve_path(cfg: dict, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path(cfg["_project_root"]) / path


def _scenario_estimate(
    cfg: dict,
    estimator: str,
    *,
    n_scale: float = 1.0,
    angle_shift_deg: float = 0.0,
    fit_range_cm1: list[float] | tuple[float, float] | None = None,
    preprocessing_override: dict[str, Any] | None = None,
    peak_prominence: float | None = None,
) -> tuple[float, dict[str, float]]:
    raw_dir = _resolve_path(cfg, cfg["paths"]["raw_dir"])
    base_fn = build_refractive_index(cfg["refractive_index"]["layer"])

    def n_fn(wn):
        base = np.asarray(base_fn(wn), dtype=complex)
        return np.real(base) * float(n_scale) + 1j * np.imag(base)

    preprocessing_cfg = deepcopy(cfg["preprocessing"])
    preprocessing_cfg.update(preprocessing_override or {})
    fit_range = fit_range_cm1 or cfg["fit"]["primary_range_cm1"]
    prominence = float(
        peak_prominence
        if peak_prominence is not None
        else cfg["estimation"].get("peak_prominence", 0.25)
    )

    values: list[float] = []
    per_dataset: dict[str, float] = {}
    for item in cfg["datasets"]:
        raw = load_spectrum_excel(
            raw_dir / item["filename"],
            item["name"],
            float(item["angle_deg"]) + float(angle_shift_deg),
            drop_first_zero=preprocessing_cfg.get("drop_first_zero", True),
        )
        proc = preprocess_spectrum(crop_spectrum(raw, fit_range), preprocessing_cfg)
        n = n_fn(proc.wavenumber_cm1)
        x = corrected_wavenumber(proc.wavenumber_cm1, n, proc.raw.angle_deg)
        fft = estimate_fft_thickness(
            x,
            proc.normalized,
            thickness_bounds_um=cfg["estimation"]["thickness_bounds_um"],
            min_cycles=cfg["estimation"].get("fft_min_cycles", 2.0),
        )
        peak = estimate_peak_regression(
            x,
            proc.normalized,
            kind="peak",
            prominence=prominence,
            distance=cfg["estimation"].get("peak_distance", 8),
            fundamental_frequency=fft.fundamental_frequency,
        ).thickness_um

        if estimator == "peak_only":
            local = [float(peak)]
        elif estimator == "fundamental_consensus":
            valley = estimate_peak_regression(
                x,
                proc.normalized,
                kind="valley",
                prominence=prominence,
                distance=cfg["estimation"].get("peak_distance", 8),
                fundamental_frequency=fft.fundamental_frequency,
            ).thickness_um
            hilbert = estimate_hilbert_thickness(
                x,
                proc.normalized,
                fft.fundamental_frequency,
                band_ratio=tuple(cfg["estimation"].get("hilbert_band_ratio", [0.55, 1.45])),
            ).thickness_um
            local = [float(peak), float(valley), float(hilbert)]
        else:
            raise ValueError(f"敏感性分析不支持估计器：{estimator}")

        values.extend(local)
        per_dataset[str(item["name"])] = float(np.median(local))

    return float(np.median(values)), per_dataset


def _default_scenarios(cfg: dict) -> list[dict]:
    material = str(cfg.get("material", "")).lower()
    primary = list(map(float, cfg["fit"]["primary_range_cm1"]))
    scenarios: list[dict] = [
        {"name": "baseline", "group": "reference", "tier": "core"},
        {"name": "n_scale_minus_0p5pct", "group": "refractive_index", "tier": "core", "n_scale": 0.995},
        {"name": "n_scale_plus_0p5pct", "group": "refractive_index", "tier": "core", "n_scale": 1.005},
        {"name": "n_scale_minus_1pct", "group": "refractive_index", "tier": "stress", "n_scale": 0.99},
        {"name": "n_scale_plus_1pct", "group": "refractive_index", "tier": "stress", "n_scale": 1.01},
        {"name": "angle_minus_0p2deg", "group": "angle", "tier": "core", "angle_shift_deg": -0.2},
        {"name": "angle_plus_0p2deg", "group": "angle", "tier": "core", "angle_shift_deg": 0.2},
        {"name": "sg_window_11", "group": "preprocessing", "tier": "core", "preprocessing_override": {"sg_window": 11}},
        {"name": "sg_window_31", "group": "preprocessing", "tier": "core", "preprocessing_override": {"sg_window": 31}},
        {"name": "sg_window_41", "group": "preprocessing", "tier": "core", "preprocessing_override": {"sg_window": 41}},
        {"name": "baseline_degree_2", "group": "preprocessing", "tier": "core", "preprocessing_override": {"baseline_degree": 2}},
        {"name": "baseline_degree_4", "group": "preprocessing", "tier": "core", "preprocessing_override": {"baseline_degree": 4}},
        {"name": "envelope_window_201", "group": "preprocessing", "tier": "core", "preprocessing_override": {"envelope_window": 201}},
        {"name": "envelope_window_401", "group": "preprocessing", "tier": "core", "preprocessing_override": {"envelope_window": 401}},
        {"name": "peak_prominence_0p18", "group": "peak_detection", "tier": "core", "peak_prominence": 0.18},
        {"name": "peak_prominence_0p32", "group": "peak_detection", "tier": "core", "peak_prominence": 0.32},
    ]
    if material == "sic":
        bands = [
            [1400.0, 3900.0],
            [1600.0, 3900.0],
            [1800.0, 3800.0],
            [2000.0, 3800.0],
        ]
    else:
        bands = [
            [550.0, 3300.0],
            [650.0, 3300.0],
            [750.0, 3200.0],
            [800.0, 3000.0],
        ]
    for lo, hi in bands:
        scenarios.append(
            {
                "name": f"fit_band_{int(lo)}_{int(hi)}",
                "group": "fit_band",
                "tier": "stress",
                "fit_range_cm1": [lo, hi],
            }
        )
    return scenarios


def run_sensitivity_analysis(
    cfg: dict,
    estimator: str,
    reference_um: float | None = None,
) -> tuple[pd.DataFrame, dict]:
    scenarios = cfg.get("uncertainty", {}).get("sensitivity_scenarios") or _default_scenarios(cfg)
    rows = []
    baseline = float(reference_um) if reference_um is not None else None

    for scenario in scenarios:
        kwargs = {
            key: scenario[key]
            for key in (
                "n_scale",
                "angle_shift_deg",
                "fit_range_cm1",
                "preprocessing_override",
                "peak_prominence",
            )
            if key in scenario
        }
        try:
            estimate, per_dataset = _scenario_estimate(cfg, estimator, **kwargs)
            if baseline is None and scenario.get("name") == "baseline":
                baseline = estimate
            rows.append(
                {
                    "scenario": scenario.get("name", "unnamed"),
                    "group": scenario.get("group", "other"),
                    "tier": scenario.get("tier", "core"),
                    "thickness_um": estimate,
                    "success": True,
                    "error": None,
                    **{f"{name}_um": value for name, value in per_dataset.items()},
                }
            )
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            rows.append(
                {
                    "scenario": scenario.get("name", "unnamed"),
                    "group": scenario.get("group", "other"),
                    "tier": scenario.get("tier", "core"),
                    "thickness_um": np.nan,
                    "success": False,
                    "error": str(exc),
                }
            )

    frame = pd.DataFrame(rows)
    if baseline is None:
        valid = frame.loc[frame["success"], "thickness_um"]
        baseline = float(valid.iloc[0])
    frame["reference_um"] = baseline
    frame["signed_change_um"] = frame["thickness_um"] - baseline
    frame["relative_change_pct"] = frame["signed_change_um"] / baseline * 100.0

    def bounds(tier: str) -> tuple[float, float, float]:
        values = frame.loc[(frame["success"]) & (frame["tier"] == tier), "thickness_um"].to_numpy(float)
        if values.size == 0:
            return float("nan"), float("nan"), float("nan")
        lo = float(np.min(values))
        hi = float(np.max(values))
        return lo, hi, float(max(abs(lo - baseline), abs(hi - baseline)))

    core_lo, core_hi, core_max = bounds("core")
    stress_values = frame.loc[frame["success"], "thickness_um"].to_numpy(float)
    stress_lo = float(np.min(stress_values))
    stress_hi = float(np.max(stress_values))
    stress_max = float(max(abs(stress_lo - baseline), abs(stress_hi - baseline)))
    summary = {
        "method": "one_factor_at_a_time_sensitivity",
        "estimator": estimator,
        "reference_um": baseline,
        "core_range_um": [core_lo, core_hi],
        "core_max_absolute_deviation_um": core_max,
        "stress_range_um": [stress_lo, stress_hi],
        "stress_max_absolute_deviation_um": stress_max,
        "n_successful": int(frame["success"].sum()),
        "n_failed": int((~frame["success"]).sum()),
    }
    return frame, summary
