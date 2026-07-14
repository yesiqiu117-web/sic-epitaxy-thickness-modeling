from __future__ import annotations

import pandas as pd


def summarize_band_stability(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if not df.empty and "thickness_um" in df:
        median = df["thickness_um"].median()
        df["relative_deviation_pct"] = (df["thickness_um"] - median).abs() / median * 100
    return df
