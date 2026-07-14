from __future__ import annotations

import numpy as np
from scipy.stats import chi2


def _autocorrelation(x: np.ndarray, max_lag: int):
    x = np.asarray(x, dtype=float)
    x = x - np.mean(x)
    denom = np.dot(x, x) + 1e-30
    return np.array([np.dot(x[:-lag], x[lag:]) / denom for lag in range(1, max_lag + 1)])


def residual_diagnostics(residual: np.ndarray, max_lag: int = 20) -> dict[str, float]:
    r = np.asarray(residual, dtype=float)
    n = len(r)
    if n < 5:
        return {"durbin_watson": float("nan"), "ljung_box_q": float("nan"), "ljung_box_p": float("nan")}
    dw = float(np.sum(np.diff(r) ** 2) / (np.sum(r**2) + 1e-30))
    h = min(max_lag, max(1, n // 5))
    acf = _autocorrelation(r, h)
    lags = np.arange(1, h + 1)
    q = float(n * (n + 2) * np.sum(acf**2 / (n - lags)))
    p = float(chi2.sf(q, h))
    return {
        "durbin_watson": dw,
        "ljung_box_q": q,
        "ljung_box_p": p,
        "acf_lag1": float(acf[0]),
    }
