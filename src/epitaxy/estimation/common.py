from __future__ import annotations

import numpy as np


def uniform_resample(x: np.ndarray, y: np.ndarray, n_points: int | None = None):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    order = np.argsort(x)
    x = x[order]
    y = y[order]
    n = int(n_points or len(x))
    xu = np.linspace(x.min(), x.max(), n)
    yu = np.interp(xu, x, y)
    return xu, yu


def robust_linear_fit(x: np.ndarray, y: np.ndarray):
    from scipy.optimize import least_squares

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    slope0, intercept0 = np.polyfit(x, y, 1)
    scale = 1.4826 * np.median(np.abs(y - np.median(y))) + 1e-12

    def residual(p):
        return (y - (p[0] * x + p[1])) / scale

    res = least_squares(residual, [slope0, intercept0], loss="soft_l1")
    pred = res.x[0] * x + res.x[1]
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(res.x[0]), float(res.x[1]), r2, pred
