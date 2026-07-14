from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar

from ..types import FitResult, ProcessedSpectrum
from .refractive_index import corrected_wavenumber


def _profile_dataset(
    spectrum: ProcessedSpectrum,
    n_layer: np.ndarray,
    thickness_um: float,
    stride: int = 1,
):
    """For a fixed thickness, profile out background, envelope and phase.

    The phase is represented by independent sine/cosine coefficients rather than
    being optimized nonlinearly.  This turns the joint fit into a stable 1-D
    thickness search and removes the slow multi-start phase loop.
    """
    sl = slice(None, None, max(1, int(stride)))
    wn = spectrum.wavenumber_cm1[sl]
    y = spectrum.normalized[sl]
    x = corrected_wavenumber(wn, np.asarray(n_layer)[sl], spectrum.raw.angle_deg)
    t = 2.0 * (wn - wn.min()) / max(np.ptp(wn), 1.0) - 1.0
    d_cm = float(thickness_um) * 1e-4
    phase = 4.0 * np.pi * d_cm * x
    c = np.cos(phase)
    s = np.sin(phase)
    # Slow background + slowly varying fringe amplitude for both quadratures.
    design = np.column_stack([
        np.ones_like(t), t,
        c, s, t * c, t * s,
    ])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    fitted = design @ coef
    return fitted, coef, x, y


def _joint_objective(
    spectra: list[ProcessedSpectrum],
    n_arrays: list[np.ndarray],
    thickness_um: float,
    stride: int,
) -> float:
    total = 0.0
    for spec, n in zip(spectra, n_arrays):
        fitted, _, _, y = _profile_dataset(spec, n, thickness_um, stride=stride)
        resid = y - fitted
        scale = 1.4826 * np.median(np.abs(y - np.median(y))) + 1e-12
        total += float(np.sum((resid / scale) ** 2))
    return total


def two_beam_profiled_fit(
    spectra: list[ProcessedSpectrum],
    n_functions: list,
    initial_thickness_um: float,
    thickness_bounds_um: tuple[float, float],
    phase_starts: list[float] | None = None,
    loss: str = "soft_l1",
    max_nfev: int = 5000,
) -> FitResult:
    """Joint two-angle two-beam fit with linear profiling.

    ``phase_starts``, ``loss`` and ``max_nfev`` are retained for backwards
    compatibility with the original configuration.  The new implementation
    profiles phase analytically and uses a coarse-to-fine bounded scalar search.
    """
    if len(spectra) != len(n_functions):
        raise ValueError("spectra 与 n_functions 长度必须一致。")
    lo, hi = map(float, thickness_bounds_um)
    initial = float(np.clip(initial_thickness_um, lo, hi))
    n_arrays = [fn(spec.wavenumber_cm1) for spec, fn in zip(spectra, n_functions)]

    # A local physically informed interval avoids selecting distant harmonic
    # aliases while still allowing the preliminary estimators to be imperfect.
    local_lo = max(lo, initial * 0.55)
    local_hi = min(hi, initial * 1.45)
    if local_hi <= local_lo:
        local_lo, local_hi = lo, hi

    coarse_grid = np.linspace(local_lo, local_hi, 601)
    coarse_scores = np.array([
        _joint_objective(spectra, n_arrays, d, stride=4) for d in coarse_grid
    ])
    best_i = int(np.argmin(coarse_scores))
    left = coarse_grid[max(0, best_i - 4)]
    right = coarse_grid[min(len(coarse_grid) - 1, best_i + 4)]
    if right <= left:
        left, right = local_lo, local_hi

    opt = minimize_scalar(
        lambda d: _joint_objective(spectra, n_arrays, float(d), stride=1),
        bounds=(left, right),
        method="bounded",
        options={"xatol": 1e-9, "maxiter": 500},
    )
    d = float(opt.x)

    fitted_dict: dict[str, np.ndarray] = {}
    residual_dict: dict[str, np.ndarray] = {}
    parameter_dict: dict[str, object] = {
        "optimizer": "profiled_sine_cosine_scalar_search",
        "fit_domain": "normalized_fringe",
        "coarse_interval_um": [float(local_lo), float(local_hi)],
    }
    total_n = 0
    total_rss = 0.0
    # 1 thickness + six profiled coefficients per spectrum.
    total_k = 1 + 6 * len(spectra)
    for spec, n in zip(spectra, n_arrays):
        fitted, coef, _, y = _profile_dataset(spec, n, d, stride=1)
        residual = y - fitted
        fitted_dict[spec.raw.name] = fitted
        residual_dict[spec.raw.name] = residual
        parameter_dict[f"linear_coefficients_{spec.raw.name}"] = coef.tolist()
        total_n += len(residual)
        total_rss += float(np.sum(residual**2))

    rmse = float(np.sqrt(total_rss / max(total_n, 1)))
    bic = float(total_n * np.log(total_rss / max(total_n, 1) + 1e-30) + total_k * np.log(max(total_n, 1)))
    return FitResult(
        method="joint_two_beam",
        thickness_um=d,
        success=bool(opt.success),
        metrics={
            "rmse": rmse,
            "rss": total_rss,
            "bic": bic,
            "objective": float(opt.fun),
        },
        parameters=parameter_dict,
        fitted=fitted_dict,
        residuals=residual_dict,
    )
