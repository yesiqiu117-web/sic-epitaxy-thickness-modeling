from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import load_config
from .diagnostics.harmonics import harmonic_analysis
from .diagnostics.multibeam import assess_multibeam_effect
from .diagnostics.residuals import residual_diagnostics
from .estimation.fft_init import estimate_fft_thickness
from .estimation.final_estimator import estimate_final_thickness
from .estimation.hilbert_phase import estimate_hilbert_thickness
from .estimation.joint_tmm import fit_joint_tmm
from .estimation.joint_harmonic import fit_joint_harmonic
from .estimation.peak_regression import estimate_peak_regression
from .io import crop_spectrum, load_spectrum_excel, save_dataframe
from .optics.refractive_index import build_refractive_index, corrected_wavenumber
from .optics.two_beam import two_beam_profiled_fit
from .plotting import (
    plot_bootstrap_distribution,
    plot_fft,
    plot_fit,
    plot_hilbert,
    plot_preprocessing,
    plot_sensitivity,
)
from .preprocessing import preprocess_spectrum
from .reporting import save_json
from .uncertainty.bootstrap import bootstrap_final_thickness
from .uncertainty.sensitivity import run_sensitivity_analysis
from .uncertainty.tmm_scan import run_effective_tmm_scan


def _resolve_path(cfg, value):
    path = Path(value)
    return path if path.is_absolute() else Path(cfg["_project_root"]) / path


def _prepare(cfg):
    raw_dir = _resolve_path(cfg, cfg["paths"]["raw_dir"])
    primary = cfg["fit"]["primary_range_cm1"]
    processed = []
    for item in cfg["datasets"]:
        spec = load_spectrum_excel(
            raw_dir / item["filename"],
            item["name"],
            item["angle_deg"],
            drop_first_zero=cfg["preprocessing"].get("drop_first_zero", True),
        )
        spec = crop_spectrum(spec, primary)
        processed.append(preprocess_spectrum(spec, cfg["preprocessing"]))
    return processed


def _single_method_results(processed, n_fn, cfg, output_dir: Path):
    rows, details, f0_by_name = [], {}, {}
    est_cfg = cfg["estimation"]
    dpi = cfg.get("plotting", {}).get("dpi", 180)
    for spec in processed:
        n = n_fn(spec.wavenumber_cm1)
        x = corrected_wavenumber(spec.wavenumber_cm1, n, spec.raw.angle_deg)
        fft = estimate_fft_thickness(
            x,
            spec.normalized,
            thickness_bounds_um=est_cfg["thickness_bounds_um"],
            min_cycles=est_cfg.get("fft_min_cycles", 2.0),
        )
        f0_by_name[spec.raw.name] = fft.fundamental_frequency
        peak_results = {}
        for kind in ("peak", "valley"):
            try:
                peak_results[kind] = estimate_peak_regression(
                    x,
                    spec.normalized,
                    kind=kind,
                    prominence=est_cfg.get("peak_prominence", 0.25),
                    distance=est_cfg.get("peak_distance", 8),
                    fundamental_frequency=fft.fundamental_frequency,
                )
            except ValueError:
                peak_results[kind] = None
        hilbert = estimate_hilbert_thickness(
            x,
            spec.normalized,
            fft.fundamental_frequency,
            band_ratio=est_cfg.get("hilbert_band_ratio", [0.55, 1.45]),
        )
        harmonics = harmonic_analysis(x, spec.normalized, fft.fundamental_frequency)
        save_dataframe(harmonics, output_dir / "tables" / f"harmonics_{spec.raw.name}.csv")
        plot_preprocessing(spec, output_dir / "figures" / f"preprocess_{spec.raw.name}.png", dpi)
        plot_fft(fft.frequencies, fft.amplitudes, fft.fundamental_frequency,
                 output_dir / "figures" / f"fft_{spec.raw.name}.png", dpi)
        plot_hilbert(hilbert, output_dir / "figures" / f"hilbert_{spec.raw.name}.png", dpi)

        peak_d = peak_results["peak"].thickness_um if peak_results["peak"] else np.nan
        valley_d = peak_results["valley"].thickness_um if peak_results["valley"] else np.nan
        rows.append({
            "dataset": spec.raw.name,
            "angle_deg": spec.raw.angle_deg,
            "fft_um": fft.thickness_um,
            "peak_um": peak_d,
            "valley_um": valley_d,
            "hilbert_um": hilbert.thickness_um,
            "hilbert_r2": hilbert.r2,
            "h2_h1": float(harmonics.loc[harmonics.harmonic == 2, "ratio_to_fundamental"].iloc[0]),
            "h3_h1": float(harmonics.loc[harmonics.harmonic == 3, "ratio_to_fundamental"].iloc[0]),
            "outlier_count": int(spec.outlier_mask.sum()),
        })
        details[spec.raw.name] = {
            "fft_candidates_um": fft.candidates_um,
            "peak_r2": peak_results["peak"].r2 if peak_results["peak"] else None,
            "valley_r2": peak_results["valley"].r2 if peak_results["valley"] else None,
            "data_metadata": spec.raw.metadata,
        }
    return pd.DataFrame(rows), details, f0_by_name


def _band_stability_results(cfg, n_fn, initial_d: float) -> pd.DataFrame:
    """Repeat phase/peak estimates on contiguous configured bands.

    The full-spectrum consensus supplies the expected fundamental so short bands
    are not allowed to jump to a harmonic alias.  These rows quantify frequency-
    band sensitivity; they are not bootstrap confidence intervals.
    """
    raw_dir = _resolve_path(cfg, cfg["paths"]["raw_dir"])
    ranges = [cfg["fit"]["primary_range_cm1"]] + list(
        cfg["fit"].get("validation_ranges_cm1", [])
    )
    expected_f0 = 2.0 * float(initial_d) * 1e-4
    rows: list[dict] = []
    for band_index, band in enumerate(ranges):
        lo, hi = map(float, band)
        band_label = "primary" if band_index == 0 else f"validation_{band_index}"
        for item in cfg["datasets"]:
            try:
                raw = load_spectrum_excel(
                    raw_dir / item["filename"],
                    item["name"],
                    item["angle_deg"],
                    drop_first_zero=cfg["preprocessing"].get("drop_first_zero", True),
                )
                proc = preprocess_spectrum(crop_spectrum(raw, [lo, hi]), cfg["preprocessing"])
                n = n_fn(proc.wavenumber_cm1)
                x = corrected_wavenumber(proc.wavenumber_cm1, n, proc.raw.angle_deg)
                fft = estimate_fft_thickness(
                    x, proc.normalized,
                    thickness_bounds_um=cfg["estimation"]["thickness_bounds_um"],
                    min_cycles=1.0,
                )
                estimates = {"fft": float(fft.thickness_um)}
                for kind in ("peak", "valley"):
                    try:
                        res = estimate_peak_regression(
                            x, proc.normalized, kind=kind,
                            prominence=cfg["estimation"].get("peak_prominence", 0.25),
                            distance=cfg["estimation"].get("peak_distance", 8),
                            fundamental_frequency=expected_f0,
                        )
                        estimates[kind] = float(res.thickness_um)
                    except ValueError:
                        estimates[kind] = np.nan
                try:
                    h = estimate_hilbert_thickness(
                        x, proc.normalized, expected_f0,
                        band_ratio=cfg["estimation"].get("hilbert_band_ratio", [0.55, 1.45]),
                    )
                    estimates["hilbert"] = float(h.thickness_um)
                    h_r2 = float(h.r2)
                except ValueError:
                    estimates["hilbert"] = np.nan
                    h_r2 = np.nan
                local_bounds = (
                    max(float(cfg["estimation"]["thickness_bounds_um"][0]), 0.75 * initial_d),
                    min(float(cfg["estimation"]["thickness_bounds_um"][1]), 1.25 * initial_d),
                )
                profiled = two_beam_profiled_fit(
                    [proc], [n_fn], initial_d, local_bounds, phase_starts=[0.0]
                )
                finite = np.asarray([v for v in estimates.values() if np.isfinite(v)], dtype=float)
                rows.append({
                    "band": band_label,
                    "wn_min_cm1": lo,
                    "wn_max_cm1": hi,
                    "dataset": item["name"],
                    "angle_deg": float(item["angle_deg"]),
                    "n_points": int(len(proc.wavenumber_cm1)),
                    **{f"{k}_um": v for k, v in estimates.items()},
                    "method_median_um": float(np.median(finite)) if finite.size else np.nan,
                    "profiled_two_beam_um": float(profiled.thickness_um),
                    "profiled_rmse": float(profiled.metrics["rmse"]),
                    "hilbert_r2": h_r2,
                })
            except (ValueError, RuntimeError) as exc:
                rows.append({
                    "band": band_label,
                    "wn_min_cm1": lo,
                    "wn_max_cm1": hi,
                    "dataset": item["name"],
                    "angle_deg": float(item["angle_deg"]),
                    "error": str(exc),
                })
    df = pd.DataFrame(rows)
    if not df.empty and "profiled_two_beam_um" in df:
        ref = float(initial_d)
        df["relative_to_consensus_pct"] = (df["profiled_two_beam_um"] - ref) / ref * 100.0
    return df


def run_pipeline(config_path: str | Path, mode: str) -> dict:
    cfg = load_config(config_path)
    output_dir = _resolve_path(cfg, cfg["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    processed = _prepare(cfg)
    layer_fn = build_refractive_index(cfg["refractive_index"]["layer"])
    substrate_fn = build_refractive_index(cfg["refractive_index"]["substrate"])
    single_df, details, _ = _single_method_results(processed, layer_fn, cfg, output_dir)
    save_dataframe(single_df, output_dir / "tables" / f"{cfg['analysis_name']}_single_methods.csv")

    initial_values = single_df[["fft_um", "peak_um", "valley_um", "hilbert_um"]].to_numpy().ravel()
    initial_values = initial_values[np.isfinite(initial_values)]
    initial_d = float(np.median(initial_values))
    band_df = _band_stability_results(cfg, layer_fn, initial_d)
    save_dataframe(band_df, output_dir / "tables" / f"{cfg['analysis_name']}_band_stability.csv")
    est = cfg["estimation"]
    n_functions = [layer_fn for _ in processed]
    two_beam = two_beam_profiled_fit(
        processed,
        n_functions,
        initial_d,
        tuple(est["thickness_bounds_um"]),
        est.get("phase_starts", [0.0]),
        loss=est.get("robust_loss", "soft_l1"),
        max_nfev=est.get("max_nfev", 5000),
    )
    for spec in processed:
        plot_fit(
            spec,
            two_beam.fitted[spec.raw.name],
            two_beam.residuals[spec.raw.name],
            output_dir / "figures" / f"two_beam_fit_{spec.raw.name}.png",
            cfg.get("plotting", {}).get("dpi", 180),
        )

    harmonic3 = fit_joint_harmonic(
        processed,
        n_functions,
        initial_thickness_um=initial_d,
        thickness_bounds_um=tuple(est["thickness_bounds_um"]),
        max_harmonic=3,
    )
    for spec in processed:
        plot_fit(
            spec,
            harmonic3.fitted[spec.raw.name],
            harmonic3.residuals[spec.raw.name],
            output_dir / "figures" / f"harmonic3_fit_{spec.raw.name}.png",
            cfg.get("plotting", {}).get("dpi", 180),
        )

    tmm = fit_joint_tmm(
        processed,
        [layer_fn for _ in processed],
        [substrate_fn for _ in processed],
        initial_thickness_um=two_beam.thickness_um,
        thickness_bounds_um=tuple(est["thickness_bounds_um"]),
        fit_kappa_scale=cfg["fit"].get("fit_kappa_scale", False),
        kappa_scale_bounds=tuple(cfg["fit"].get("kappa_scale_bounds", [0.1, 10.0])),
        loss=est.get("robust_loss", "soft_l1"),
        max_nfev=est.get("max_nfev", 5000),
    )
    for spec in processed:
        plot_fit(
            spec,
            tmm.fitted[spec.raw.name],
            tmm.residuals[spec.raw.name],
            output_dir / "figures" / f"tmm_fit_{spec.raw.name}.png",
            cfg.get("plotting", {}).get("dpi", 180),
        )

    residual_diag = {"two_beam": {}, "harmonic3": {}, "tmm": {}}
    for spec in processed:
        residual_diag["two_beam"][spec.raw.name] = residual_diagnostics(two_beam.residuals[spec.raw.name])
        residual_diag["harmonic3"][spec.raw.name] = residual_diagnostics(harmonic3.residuals[spec.raw.name])
        residual_diag["tmm"][spec.raw.name] = residual_diagnostics(tmm.residuals[spec.raw.name])

    final_estimator_name = cfg["fit"].get(
        "final_estimator", "peak_only" if mode == "si" else "fundamental_consensus"
    )
    final_estimate = estimate_final_thickness(single_df, final_estimator_name)
    multibeam = assess_multibeam_effect(
        single_df,
        processed,
        two_beam,
        harmonic3,
        thresholds=cfg.get("multibeam", {}),
    )

    uncertainty_cfg = cfg.get("uncertainty", {})
    bootstrap_frame = pd.DataFrame()
    bootstrap_summary = {"enabled": False}
    if uncertainty_cfg.get("bootstrap_enabled", True):
        bootstrap_frame, bootstrap_summary = bootstrap_final_thickness(
            processed,
            layer_fn,
            tuple(est["thickness_bounds_um"]),
            estimator=final_estimator_name,
            repeats=int(uncertainty_cfg.get("bootstrap_repeats", 400)),
            block_size=int(uncertainty_cfg.get("block_size", 80)),
            confidence_level=float(uncertainty_cfg.get("confidence_level", 0.95)),
            random_seed=int(cfg.get("project", {}).get("random_seed", 2025)),
            hilbert_band_ratio=tuple(est.get("hilbert_band_ratio", [0.55, 1.45])),
        )
        bootstrap_summary["enabled"] = True
        save_dataframe(
            bootstrap_frame,
            output_dir / "tables" / f"{cfg['analysis_name']}_bootstrap.csv",
        )
        plot_bootstrap_distribution(
            bootstrap_frame.loc[bootstrap_frame["success"], "thickness_um"],
            final_estimate.thickness_um,
            bootstrap_summary["ci_low_um"],
            bootstrap_summary["ci_high_um"],
            output_dir / "figures" / f"bootstrap_{cfg['analysis_name']}.png",
            cfg.get("plotting", {}).get("dpi", 180),
        )

    sensitivity_frame = pd.DataFrame()
    sensitivity_summary = {"enabled": False}
    if uncertainty_cfg.get("sensitivity_enabled", True):
        sensitivity_frame, sensitivity_summary = run_sensitivity_analysis(
            cfg, final_estimator_name, reference_um=final_estimate.thickness_um
        )
        sensitivity_summary["enabled"] = True
        save_dataframe(
            sensitivity_frame,
            output_dir / "tables" / f"{cfg['analysis_name']}_sensitivity.csv",
        )
        plot_sensitivity(
            sensitivity_frame,
            output_dir / "figures" / f"sensitivity_{cfg['analysis_name']}.png",
            cfg.get("plotting", {}).get("dpi", 180),
        )

    tmm_scan_frame, tmm_scan_summary = run_effective_tmm_scan(
        processed, cfg, final_estimate.thickness_um
    )
    if not tmm_scan_frame.empty:
        save_dataframe(
            tmm_scan_frame,
            output_dir / "tables" / f"{cfg['analysis_name']}_tmm_parameter_scan.csv",
        )

    statistical_interval = [
        bootstrap_summary.get("ci_low_um", float("nan")),
        bootstrap_summary.get("ci_high_um", float("nan")),
    ]
    core_interval = sensitivity_summary.get("core_range_um", [float("nan"), float("nan")])
    finite_lows = [v for v in (statistical_interval[0], core_interval[0]) if np.isfinite(v)]
    finite_highs = [v for v in (statistical_interval[1], core_interval[1]) if np.isfinite(v)]
    recommended_interval = [
        float(min(finite_lows)) if finite_lows else float("nan"),
        float(max(finite_highs)) if finite_highs else float("nan"),
    ]
    final_result = {
        "estimator": final_estimate.estimator,
        "thickness_um": final_estimate.thickness_um,
        "per_angle_um": final_estimate.per_angle_um,
        "cross_angle_relative_pct": final_estimate.cross_angle_relative_pct,
        "uncorrected_all_method_consensus_um": final_estimate.uncorrected_consensus_um,
        "multi_beam_correction_um": final_estimate.thickness_um - final_estimate.uncorrected_consensus_um,
        "statistical_95pct_interval_um": statistical_interval,
        "core_sensitivity_interval_um": core_interval,
        "recommended_interval_um": recommended_interval,
        "expanded_stress_interval_um": sensitivity_summary.get(
            "stress_range_um", [float("nan"), float("nan")]
        ),
        "multi_beam_classification": multibeam["classification"],
    }

    method_values = single_df[["fft_um", "peak_um", "valley_um", "hilbert_um"]].to_numpy().ravel()
    method_values = method_values[np.isfinite(method_values)]
    consensus = {
        "median_um": float(np.median(method_values)),
        "method_min_um": float(np.min(method_values)),
        "method_max_um": float(np.max(method_values)),
        "q25_um": float(np.quantile(method_values, 0.25)),
        "q75_um": float(np.quantile(method_values, 0.75)),
        "note": "该区间为跨角度、跨方法离散范围，不等同于统计置信区间。",
    }

    summary = {
        "analysis_name": cfg["analysis_name"],
        "mode": mode,
        "material": cfg.get("material"),
        "warning": "外延层折射率采用给定配置中的光学模型；衬底掺杂与吸收参数未知，因此 TMM 参数扫描只用于敏感性与可辨识性分析，不作为唯一厚度反演。",
        "final_result": final_result,
        "multibeam_assessment": multibeam,
        "bootstrap_uncertainty": bootstrap_summary,
        "sensitivity_analysis": sensitivity_summary,
        "tmm_parameter_scan": tmm_scan_summary,
        "initial_thickness_um": initial_d,
        "robust_consensus": consensus,
        "single_methods": single_df.to_dict(orient="records"),
        "single_details": details,
        "band_stability": band_df.replace({np.nan: None}).to_dict(orient="records"),
        "joint_two_beam": {
            "thickness_um": two_beam.thickness_um,
            "success": two_beam.success,
            "metrics": two_beam.metrics,
            "parameters": two_beam.parameters,
        },
        "joint_harmonic3": {
            "thickness_um": harmonic3.thickness_um,
            "success": harmonic3.success,
            "metrics": harmonic3.metrics,
            "parameters": harmonic3.parameters,
        },
        "joint_tmm": {
            "thickness_um": tmm.thickness_um,
            "success": tmm.success,
            "metrics": tmm.metrics,
            "parameters": tmm.parameters,
        },
        "model_comparison": {
            "delta_bic_two_minus_harmonic3": two_beam.metrics["bic"] - harmonic3.metrics["bic"],
            "delta_bic_two_minus_tmm": two_beam.metrics["bic"] - tmm.metrics["bic"],
            "harmonic3_correction_um": harmonic3.thickness_um - two_beam.thickness_um,
            "tmm_correction_um": tmm.thickness_um - two_beam.thickness_um,
            "interpretation": "BIC 差值为正表示右侧复杂模型优于双光束模型。",
        },
        "residual_diagnostics": residual_diag,
    }
    save_json(summary, output_dir / "reports" / f"{cfg['analysis_name']}_summary.json")
    comparison = pd.DataFrame([
        {"model": "two_beam", "thickness_um": two_beam.thickness_um, **two_beam.metrics},
        {"model": "harmonic3", "thickness_um": harmonic3.thickness_um, **harmonic3.metrics},
        {"model": "tmm", "thickness_um": tmm.thickness_um, **tmm.metrics},
    ])
    save_dataframe(comparison, output_dir / "tables" / f"{cfg['analysis_name']}_model_comparison.csv")
    return summary


def run_sic(config_path="configs/q2_sic.yaml"):
    return run_pipeline(config_path, mode="sic")


def run_si(config_path="configs/q3_si.yaml"):
    return run_pipeline(config_path, mode="si")
