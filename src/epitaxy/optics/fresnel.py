from __future__ import annotations

import numpy as np


def cos_theta_in_medium(n0: complex | np.ndarray, n: np.ndarray, theta0_rad: float):
    n = np.asarray(n, dtype=complex)
    sin_theta = np.asarray(n0, dtype=complex) * np.sin(theta0_rad) / n
    cos_theta = np.sqrt(1.0 - sin_theta**2 + 0j)
    # 选择衰减/向前传播分支。
    flip = np.real(cos_theta) < 0
    cos_theta[flip] *= -1
    return cos_theta


def fresnel_r(
    ni: np.ndarray,
    nj: np.ndarray,
    cos_i: np.ndarray,
    cos_j: np.ndarray,
    polarization: str,
) -> np.ndarray:
    if polarization == "s":
        return (ni * cos_i - nj * cos_j) / (ni * cos_i + nj * cos_j)
    if polarization == "p":
        return (nj * cos_i - ni * cos_j) / (nj * cos_i + ni * cos_j)
    raise ValueError("polarization 必须为 's' 或 'p'。")
