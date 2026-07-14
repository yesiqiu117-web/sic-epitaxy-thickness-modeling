from __future__ import annotations

import numpy as np

from .fresnel import cos_theta_in_medium, fresnel_r


def single_layer_reflectance(
    wavenumber_cm1: np.ndarray,
    thickness_um: float,
    angle_deg: float,
    n_layer: np.ndarray,
    n_substrate: np.ndarray,
    n_ambient: complex = 1.0 + 0j,
    polarization: str = "unpolarized",
) -> np.ndarray:
    """单层膜 Airy/TMM 反射率。

    约定复折射率写作 n + i*kappa，并通过传播因子自动体现吸收。
    为保证正向传播衰减，传播指数采用 exp(2j*beta)，其中 beta 的虚部为正。
    """
    wn = np.asarray(wavenumber_cm1, dtype=float)
    n1 = np.asarray(n_layer, dtype=complex)
    n2 = np.asarray(n_substrate, dtype=complex)
    n0 = np.full_like(n1, n_ambient, dtype=complex)
    theta0 = np.deg2rad(angle_deg)
    cos0 = np.full_like(n1, np.cos(theta0), dtype=complex)
    cos1 = cos_theta_in_medium(n_ambient, n1, theta0)
    cos2 = cos_theta_in_medium(n_ambient, n2, theta0)
    d_cm = float(thickness_um) * 1e-4
    beta = 2.0 * np.pi * wn * d_cm * n1 * cos1
    propagation = np.exp(2j * beta)

    def reflectance(pol: str):
        r01 = fresnel_r(n0, n1, cos0, cos1, pol)
        r12 = fresnel_r(n1, n2, cos1, cos2, pol)
        r = (r01 + r12 * propagation) / (1.0 + r01 * r12 * propagation)
        return np.abs(r) ** 2

    if polarization == "s":
        return reflectance("s")
    if polarization == "p":
        return reflectance("p")
    if polarization == "unpolarized":
        return 0.5 * (reflectance("s") + reflectance("p"))
    raise ValueError("polarization 必须为 s、p 或 unpolarized。")
