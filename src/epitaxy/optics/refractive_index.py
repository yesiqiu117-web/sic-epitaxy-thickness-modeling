from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


ComplexIndexFunction = Callable[[np.ndarray], np.ndarray]


def _apply_modifiers(base_fn: ComplexIndexFunction, cfg: dict) -> ComplexIndexFunction:
    n_scale = float(cfg.get("n_scale", 1.0))
    n_offset = float(cfg.get("n_offset", 0.0))
    k_scale = float(cfg.get("kappa_scale", 1.0))
    k_offset = float(cfg.get("kappa_offset", 0.0))

    def wrapped(wn):
        value = np.asarray(base_fn(wn), dtype=complex)
        real = np.real(value) * n_scale + n_offset
        imag = np.imag(value) * k_scale + k_offset
        return real + 1j * imag

    return wrapped


def build_refractive_index(cfg: dict) -> ComplexIndexFunction:
    model = str(cfg.get("model", "constant")).lower()
    kappa_default = float(cfg.get("kappa", 0.0))

    if model == "constant":
        n0 = float(cfg["n"])
        base = lambda wn: np.full_like(
            np.asarray(wn, dtype=float), n0 + 1j * kappa_default, dtype=complex
        )
        return _apply_modifiers(base, cfg)

    if model == "cauchy":
        A = float(cfg["A"])
        B = float(cfg.get("B", 0.0))
        C = float(cfg.get("C", 0.0))

        def base(wn):
            wn = np.asarray(wn, dtype=float)
            lam_um = 1e4 / wn
            n = A + B / lam_um**2 + C / lam_um**4
            return n.astype(complex) + 1j * kappa_default

        return _apply_modifiers(base, cfg)

    if model == "sellmeier":
        B = np.asarray(cfg["B"], dtype=float)
        C = np.asarray(cfg["C"], dtype=float)
        if len(B) != len(C):
            raise ValueError("Sellmeier 的 B 与 C 长度必须一致。")

        def base(wn):
            wn = np.asarray(wn, dtype=float)
            lam2 = (1e4 / wn) ** 2
            n2 = np.ones_like(lam2)
            for bi, ci in zip(B, C):
                n2 += bi * lam2 / (lam2 - ci)
            return np.sqrt(n2).astype(complex) + 1j * kappa_default

        return _apply_modifiers(base, cfg)

    if model == "chandler_horowitz_si":
        # Chandler-Horowitz & Amirtharaj, J. Appl. Phys. 97, 123526 (2005).
        # λ is in μm; validity: 2.5–22.2 μm (450–4000 cm^-1).
        def base(wn):
            wn = np.asarray(wn, dtype=float)
            lam_um = 1e4 / wn
            n2 = (
                11.67316
                + 1.0 / lam_um**2
                + 0.004482633 / (lam_um**2 - 1.108205**2)
            )
            return np.sqrt(n2).astype(complex) + 1j * kappa_default

        return _apply_modifiers(base, cfg)

    if model == "phonon_tolo":
        # Lossy one-phonon factorized dielectric function.  Wavenumbers and
        # damping parameters are in cm^-1.
        eps_inf = float(cfg["epsilon_inf"])
        to_cm1 = float(cfg["to_cm1"])
        lo_cm1 = float(cfg["lo_cm1"])
        gamma_to = float(cfg.get("gamma_to_cm1", cfg.get("gamma_cm1", 0.0)))
        gamma_lo = float(cfg.get("gamma_lo_cm1", cfg.get("gamma_cm1", 0.0)))

        def base(wn):
            wn = np.asarray(wn, dtype=float)
            numerator = lo_cm1**2 - wn**2 - 1j * gamma_lo * wn
            denominator = to_cm1**2 - wn**2 - 1j * gamma_to * wn
            eps = eps_inf * numerator / denominator
            n_complex = np.sqrt(eps.astype(complex))
            # Select the passive branch.
            n_complex = np.where(np.imag(n_complex) < 0, np.conj(n_complex), n_complex)
            return n_complex

        return _apply_modifiers(base, cfg)

    if model == "polynomial_wn":
        coefficients = np.asarray(cfg["coefficients"], dtype=float)
        center = float(cfg.get("center", 0.0))
        scale = float(cfg.get("scale", 1.0))

        def base(wn):
            wn = np.asarray(wn, dtype=float)
            z = (wn - center) / scale
            n = sum(c * z**i for i, c in enumerate(coefficients))
            return np.asarray(n, dtype=complex) + 1j * kappa_default

        return _apply_modifiers(base, cfg)

    if model == "table":
        path = Path(cfg["path"])
        table = pd.read_csv(path)
        required = {"wavenumber_cm1", "n"}
        if not required.issubset(table.columns):
            raise ValueError(f"折射率表必须包含列 {sorted(required)}")
        table = table.sort_values("wavenumber_cm1")
        x = table["wavenumber_cm1"].to_numpy(float)
        n = table["n"].to_numpy(float)
        k = (
            table["kappa"].to_numpy(float)
            if "kappa" in table
            else np.full_like(n, kappa_default)
        )

        def base(wn):
            wn = np.asarray(wn, dtype=float)
            return np.interp(wn, x, n) + 1j * np.interp(wn, x, k)

        return _apply_modifiers(base, cfg)

    raise ValueError(f"不支持的折射率模型：{model}")


def corrected_wavenumber(
    wavenumber_cm1: np.ndarray,
    n_layer: np.ndarray,
    angle_deg: float,
) -> np.ndarray:
    wn = np.asarray(wavenumber_cm1, dtype=float)
    n = np.real(np.asarray(n_layer))
    theta = np.deg2rad(angle_deg)
    value = n**2 - np.sin(theta) ** 2
    if np.any(value <= 0):
        raise ValueError("修正波数出现非正根，请检查折射率和入射角。")
    return wn * np.sqrt(value)
