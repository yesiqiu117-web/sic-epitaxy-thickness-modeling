from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .types import Spectrum


def load_spectrum_excel(
    path: str | Path,
    name: str,
    angle_deg: float,
    drop_first_zero: bool = True,
) -> Spectrum:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"未找到数据文件：{path}。请将官方附件放入配置指定的 raw_dir。"
        )
    df = pd.read_excel(path)
    if df.shape[1] < 2:
        raise ValueError(f"{path} 至少需要两列：波数和反射率。")
    wn = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    r = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    clean = pd.DataFrame({"wn": wn, "r": r}).dropna()
    clean = clean.groupby("wn", as_index=False)["r"].mean().sort_values("wn")
    if drop_first_zero and len(clean) > 1 and np.isclose(clean.iloc[0]["r"], 0.0):
        typical = np.nanmedian(np.abs(clean.iloc[1:]["r"].to_numpy()))
        if typical > 0:
            clean = clean.iloc[1:].copy()
    wn_arr = clean["wn"].to_numpy(dtype=float)
    r_arr = clean["r"].to_numpy(dtype=float)
    metadata = {
        "source": str(path),
        "n_points": int(len(clean)),
        "wn_min": float(wn_arr.min()),
        "wn_max": float(wn_arr.max()),
        "reflectance_min": float(r_arr.min()),
        "reflectance_max": float(r_arr.max()),
        "fraction_above_100": float(np.mean(r_arr > 100.0)),
        "median_step": float(np.median(np.diff(wn_arr))) if len(wn_arr) > 1 else float("nan"),
    }
    return Spectrum(name, angle_deg, wn_arr, r_arr, metadata)


def crop_spectrum(spectrum: Spectrum, range_cm1: Iterable[float]) -> Spectrum:
    lo, hi = map(float, range_cm1)
    mask = (spectrum.wavenumber_cm1 >= lo) & (spectrum.wavenumber_cm1 <= hi)
    if mask.sum() < 20:
        raise ValueError(
            f"{spectrum.name} 在区间 [{lo}, {hi}] 内有效点少于 20 个。"
        )
    meta = dict(spectrum.metadata)
    meta.update({"crop_min": lo, "crop_max": hi, "crop_n_points": int(mask.sum())})
    return Spectrum(
        spectrum.name,
        spectrum.angle_deg,
        spectrum.wavenumber_cm1[mask],
        spectrum.reflectance[mask],
        meta,
    )


def save_dataframe(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
