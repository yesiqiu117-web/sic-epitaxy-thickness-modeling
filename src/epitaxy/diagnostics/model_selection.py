from __future__ import annotations

import numpy as np


def information_criteria(residual: np.ndarray, n_parameters: int) -> dict[str, float]:
    residual = np.asarray(residual, dtype=float)
    n = len(residual)
    rss = float(np.sum(residual**2))
    variance = rss / max(n, 1)
    aic = float(n * np.log(variance + 1e-30) + 2 * n_parameters)
    bic = float(n * np.log(variance + 1e-30) + n_parameters * np.log(max(n, 1)))
    return {"rss": rss, "rmse": float(np.sqrt(variance)), "aic": aic, "bic": bic}
