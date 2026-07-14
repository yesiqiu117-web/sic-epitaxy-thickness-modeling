from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epitaxy.optics.tmm import single_layer_reflectance


def two_beam_data(wn, d_um, angle, n=2.60, seed=0):
    rng = np.random.default_rng(seed)
    x = wn * np.sqrt(n**2 - np.sin(np.deg2rad(angle)) ** 2)
    phase = 4 * np.pi * d_um * 1e-4 * x + 0.4
    baseline = 35 + 0.003 * (wn - wn.mean())
    envelope = 8 + 1.5 * np.sin(2 * np.pi * (wn - wn.min()) / np.ptp(wn))
    return baseline + envelope * np.cos(phase) + rng.normal(0, 0.35, len(wn))


def tmm_data(wn, d_um, angle, n1, n2, seed=0):
    rng = np.random.default_rng(seed)
    n1_arr = np.full_like(wn, n1, dtype=complex)
    n2_arr = np.full_like(wn, n2, dtype=complex)
    r = single_layer_reflectance(wn, d_um, angle, n1_arr, n2_arr)
    baseline = 3 + 0.001 * (wn - wn.mean())
    return baseline + 90 * r + rng.normal(0, 0.20, len(wn))


def main():
    out = ROOT / "data" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    wn_sic = np.linspace(800, 4500, 2600)
    for idx, angle in enumerate((10.0, 15.0), start=1):
        r = two_beam_data(wn_sic, 12.5, angle, seed=100 + idx)
        pd.DataFrame({"波数(cm-1)": wn_sic, "反射率(%)": r}).to_excel(
            out / f"synthetic_附件{idx}.xlsx", index=False
        )
    wn_si = np.linspace(450, 3800, 2600)
    for idx, angle in zip((3, 4), (10.0, 15.0)):
        r = tmm_data(wn_si, 18.0, angle, 3.42 + 0.003j, 3.55 + 0.025j, seed=100 + idx)
        pd.DataFrame({"波数(cm-1)": wn_si, "反射率(%)": r}).to_excel(
            out / f"synthetic_附件{idx}.xlsx", index=False
        )
    print(f"Synthetic data written to {out}")


if __name__ == "__main__":
    main()
