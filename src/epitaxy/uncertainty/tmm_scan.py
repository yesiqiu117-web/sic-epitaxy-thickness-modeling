from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from itertools import product

import numpy as np
import pandas as pd

from ..estimation.joint_tmm import fit_joint_tmm
from ..optics.refractive_index import build_refractive_index
from ..types import ProcessedSpectrum


def run_effective_tmm_scan(
    processed: list[ProcessedSpectrum],
    cfg: dict,
    initial_thickness_um: float,
) -> tuple[pd.DataFrame, dict]:
    """Profile unknown substrate optical constants over a bounded grid.

    The scan is deliberately reported as an identifiability/sensitivity result,
    not as a unique inversion of substrate doping parameters.
    """
    scan_cfg = cfg.get("uncertainty", {}).get("tmm_scan", {})
    if not scan_cfg.get("enabled", True):
        return pd.DataFrame(), {"enabled": False}

    substrate_base = deepcopy(cfg["refractive_index"]["substrate"])
    stride = max(1, int(scan_cfg.get("data_stride", 8)))
    scan_spectra = [
        replace(
            spec,
            wavenumber_cm1=spec.wavenumber_cm1[::stride],
            reflectance=spec.reflectance[::stride],
            smoothed=spec.smoothed[::stride],
            baseline=spec.baseline[::stride],
            residual=spec.residual[::stride],
            envelope=spec.envelope[::stride],
            normalized=spec.normalized[::stride],
            outlier_mask=spec.outlier_mask[::stride],
        )
        for spec in processed
    ]
    axes = scan_cfg.get("axes") or {}
    if not axes:
        material = str(cfg.get("material", "")).lower()
        if material == "sic":
            axes = {
                "n_scale": [1.00, 1.02, 1.04],
                "kappa_offset": [0.0, 0.01, 0.03],
            }
        else:
            axes = {
                "n_offset": [0.0, 0.04, 0.08],
                "kappa": [0.005, 0.02, 0.05],
            }

    names = list(axes)
    values = [list(map(float, axes[name])) for name in names]
    layer_fn = build_refractive_index(cfg["refractive_index"]["layer"])
    rows = []
    for combination in product(*values):
        substrate_cfg = deepcopy(substrate_base)
        settings = dict(zip(names, combination))
        substrate_cfg.update(settings)
        substrate_fn = build_refractive_index(substrate_cfg)
        try:
            fit = fit_joint_tmm(
                scan_spectra,
                [layer_fn for _ in scan_spectra],
                [substrate_fn for _ in scan_spectra],
                initial_thickness_um=initial_thickness_um,
                thickness_bounds_um=tuple(cfg["estimation"]["thickness_bounds_um"]),
                fit_kappa_scale=False,
                loss=cfg["estimation"].get("robust_loss", "soft_l1"),
                max_nfev=cfg["estimation"].get("max_nfev", 5000),
            )
            rows.append(
                {
                    **settings,
                    "thickness_um": float(fit.thickness_um),
                    "rmse": float(fit.metrics["rmse"]),
                    "bic": float(fit.metrics["bic"]),
                    "success": bool(fit.success),
                }
            )
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            rows.append({**settings, "success": False, "error": str(exc)})

    frame = pd.DataFrame(rows)
    valid = frame.loc[frame["success"]].copy()
    if valid.empty:
        summary = {"enabled": True, "n_successful": 0, "n_failed": int(len(frame))}
    else:
        best = valid.loc[valid["bic"].idxmin()]
        summary = {
            "enabled": True,
            "interpretation": "衬底光学常数未知时的有界敏感性扫描，不代表参数被唯一识别；为控制计算量，扫描使用等距降采样。",
            "data_stride": stride,
            "n_successful": int(len(valid)),
            "n_failed": int(len(frame) - len(valid)),
            "best_bic": float(best["bic"]),
            "best_rmse": float(best["rmse"]),
            "best_thickness_um": float(best["thickness_um"]),
            "thickness_range_um": [
                float(valid["thickness_um"].min()),
                float(valid["thickness_um"].max()),
            ],
            "best_settings": {name: float(best[name]) for name in names},
        }
    return frame, summary
