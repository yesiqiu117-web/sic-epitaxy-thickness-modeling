from __future__ import annotations

import numpy as np
from scipy.optimize import differential_evolution, minimize, minimize_scalar
from scipy.signal import savgol_filter

from ..optics.tmm import single_layer_reflectance
from ..types import FitResult, ProcessedSpectrum


def _valid_odd_window(requested: int, n: int, polyorder: int = 2) -> int:
    w = min(int(requested), n if n % 2 else n - 1)
    w = max(w, polyorder + 3)
    if w % 2 == 0:
        w -= 1
    return max(w, polyorder + 1)


def _normalize_physical(wn: np.ndarray, physical: np.ndarray) -> np.ndarray:
    """Map a physical TMM reflectance to the same fringe domain as the data.

    Thickness and multi-beam waveform are identified from phase/shape, while
    unknown instrument response and substrate doping mainly affect slow baseline
    and amplitude.  Removing those slow components avoids a false thickness shift.
    """
    wn = np.asarray(wn, dtype=float)
    y = np.asarray(physical, dtype=float)
    z = (wn - wn.mean()) / max(np.ptp(wn), 1.0)
    coef = np.polyfit(z, y, 3)
    residual = y - np.polyval(coef, z)
    w = _valid_odd_window(max(101, len(y) // 18), len(y), 2)
    envelope = savgol_filter(np.abs(residual), w, 2)
    floor = 0.06 * max(np.percentile(np.abs(residual), 90), 1e-12)
    normalized = residual / np.maximum(envelope, floor)
    med = np.median(normalized)
    scale = 1.4826 * np.median(np.abs(normalized - med)) + 1e-12
    return (normalized - med) / scale


def _profile_calibration(y: np.ndarray, physical_norm: np.ndarray, wn: np.ndarray):
    t = 2.0 * (wn - wn.min()) / max(np.ptp(wn), 1.0) - 1.0
    design = np.column_stack([
        np.ones_like(t), t,
        physical_norm, t * physical_norm,
    ])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    fitted = design @ coef
    return fitted, coef


def _objective(
    p: np.ndarray,
    spectra: list[ProcessedSpectrum],
    layer_arrays: list[np.ndarray],
    substrate_arrays: list[np.ndarray],
    fit_kappa_scale: bool,
    stride: int,
) -> float:
    d = float(p[0])
    k_scale = float(p[1]) if fit_kappa_scale else 1.0
    total = 0.0
    sl = slice(None, None, max(1, int(stride)))
    for spec, n1_full, n2_full in zip(spectra, layer_arrays, substrate_arrays):
        wn = spec.wavenumber_cm1[sl]
        y = spec.normalized[sl]
        n1_raw = n1_full[sl]
        n1 = np.real(n1_raw) + 1j * np.imag(n1_raw) * k_scale
        n2 = n2_full[sl]
        physical = single_layer_reflectance(wn, d, spec.raw.angle_deg, n1, n2)
        physical_norm = _normalize_physical(wn, physical)
        fitted, _ = _profile_calibration(y, physical_norm, wn)
        resid = y - fitted
        total += float(np.sum(resid**2))
    return total


def fit_joint_tmm(
    spectra: list[ProcessedSpectrum],
    layer_functions: list,
    substrate_functions: list,
    initial_thickness_um: float,
    thickness_bounds_um=(1.0, 1000.0),
    fit_kappa_scale: bool = False,
    kappa_scale_bounds=(0.1, 10.0),
    loss: str = "soft_l1",
    max_nfev: int = 5000,
) -> FitResult:
    if not (len(spectra) == len(layer_functions) == len(substrate_functions)):
        raise ValueError("TMM 输入列表长度不一致。")

    lo, hi = map(float, thickness_bounds_um)
    initial = float(np.clip(initial_thickness_um, lo, hi))
    d_lo = max(lo, initial * 0.75)
    d_hi = min(hi, initial * 1.25)
    if d_hi <= d_lo:
        d_lo, d_hi = lo, hi
    k_lo, k_hi = map(float, kappa_scale_bounds)

    layer_arrays = [fn(spec.wavenumber_cm1) for spec, fn in zip(spectra, layer_functions)]
    substrate_arrays = [fn(spec.wavenumber_cm1) for spec, fn in zip(spectra, substrate_functions)]

    if not fit_kappa_scale:
        grid = np.linspace(d_lo, d_hi, 401)
        scores = np.array([
            _objective(np.array([d]), spectra, layer_arrays, substrate_arrays, False, stride=5)
            for d in grid
        ])
        i = int(np.argmin(scores))
        left = grid[max(0, i - 4)]
        right = grid[min(len(grid) - 1, i + 4)]
        opt = minimize_scalar(
            lambda d: _objective(np.array([d]), spectra, layer_arrays, substrate_arrays, False, stride=1),
            bounds=(left, right),
            method="bounded",
            options={"xatol": 1e-9, "maxiter": 500},
        )
        p_opt = np.array([float(opt.x)])
        success = bool(opt.success)
        optimizer_name = "coarse_grid_plus_bounded_scalar"
    else:
        bounds = [(d_lo, d_hi), (k_lo, k_hi)]
        global_opt = differential_evolution(
            lambda p: _objective(np.asarray(p), spectra, layer_arrays, substrate_arrays, True, stride=6),
            bounds=bounds,
            seed=2025,
            popsize=8,
            maxiter=30,
            tol=1e-7,
            polish=False,
            workers=1,
        )
        local_opt = minimize(
            lambda p: _objective(np.asarray(p), spectra, layer_arrays, substrate_arrays, True, stride=1),
            x0=np.asarray(global_opt.x, dtype=float),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 300, "ftol": 1e-12},
        )
        p_opt = np.asarray(local_opt.x, dtype=float)
        success = bool(global_opt.success or local_opt.success)
        optimizer_name = "differential_evolution_plus_lbfgsb"

    d = float(p_opt[0])
    k_scale = float(p_opt[1]) if fit_kappa_scale else 1.0
    fitted_dict: dict[str, np.ndarray] = {}
    residual_dict: dict[str, np.ndarray] = {}
    params: dict[str, object] = {
        "kappa_scale": k_scale,
        "optimizer": optimizer_name,
        "search_interval_um": [float(d_lo), float(d_hi)],
        "fit_domain": "normalized_fringe",
    }
    total_n = 0
    total_rss = 0.0
    total_k = 1 + int(fit_kappa_scale) + 4 * len(spectra)
    for spec, n1_raw, n2 in zip(spectra, layer_arrays, substrate_arrays):
        wn = spec.wavenumber_cm1
        n1 = np.real(n1_raw) + 1j * np.imag(n1_raw) * k_scale
        physical = single_layer_reflectance(wn, d, spec.raw.angle_deg, n1, n2)
        physical_norm = _normalize_physical(wn, physical)
        fitted, coef = _profile_calibration(spec.normalized, physical_norm, wn)
        residual = spec.normalized - fitted
        fitted_dict[spec.raw.name] = fitted
        residual_dict[spec.raw.name] = residual
        params[f"calibration_{spec.raw.name}"] = coef.tolist()
        total_n += len(residual)
        total_rss += float(np.sum(residual**2))

    rmse = float(np.sqrt(total_rss / max(total_n, 1)))
    bic = float(total_n * np.log(total_rss / max(total_n, 1) + 1e-30) + total_k * np.log(max(total_n, 1)))
    return FitResult(
        method="joint_tmm",
        thickness_um=d,
        success=success,
        metrics={"rmse": rmse, "rss": total_rss, "bic": bic},
        parameters=params,
        fitted=fitted_dict,
        residuals=residual_dict,
    )
