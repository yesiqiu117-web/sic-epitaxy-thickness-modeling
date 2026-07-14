from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def _convert(value: Any):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _convert(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_convert(v) for v in value]
    return value


def save_json(data: dict, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(_convert(data), f, ensure_ascii=False, indent=2)


def save_text(text: str, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def final_results_dataframe(sic: dict, si: dict):
    import pandas as pd

    rows = []
    for task, summary in [
        ("Q2_SiC", sic),
        ("Q3_Si", si),
    ]:
        final = summary["final_result"]
        mb = summary["multibeam_assessment"]
        rows.append(
            {
                "task": task,
                "material": summary.get("material"),
                "final_estimator": final["estimator"],
                "thickness_um": final["thickness_um"],
                "stat_ci_low_um": final["statistical_95pct_interval_um"][0],
                "stat_ci_high_um": final["statistical_95pct_interval_um"][1],
                "recommended_low_um": final["recommended_interval_um"][0],
                "recommended_high_um": final["recommended_interval_um"][1],
                "stress_low_um": final["expanded_stress_interval_um"][0],
                "stress_high_um": final["expanded_stress_interval_um"][1],
                "cross_angle_relative_pct": final["cross_angle_relative_pct"],
                "multi_beam_classification": final["multi_beam_classification"],
                "peak_valley_relative_pct": mb["peak_valley_median_relative_pct"],
                "median_h2_h1": mb["median_h2_h1"],
                "multi_beam_correction_um": final["multi_beam_correction_um"],
            }
        )
    return pd.DataFrame(rows)


def combined_markdown_report(sic: dict, si: dict) -> str:
    s_final = sic["final_result"]
    i_final = si["final_result"]
    s_mb = sic["multibeam_assessment"]
    i_mb = si["multibeam_assessment"]

    def interval(values):
        return f"[{values[0]:.4f}, {values[1]:.4f}]"

    return f"""# 2025 国赛 B 题完整实验结果

## 1. 完成范围

本仓库已经完成以下四个工作包：

1. 问题 1：双光束干涉模型推导与代码映射；
2. 问题 2：附件 1、2 的 SiC 厚度计算与可靠性分析；
3. 问题 3：附件 3、4 的多光束判定及 Si 厚度计算；
4. 问题 3 补充：SiC 多光束影响复核、基频修正和修正后结果。

## 2. 最终数值结果

| 材料 | 最终方法 | 厚度/μm | 分块 Bootstrap 95% 区间/μm | 推荐区间/μm | 双角度相对差 |
|---|---|---:|---:|---:|---:|
| SiC | 基频峰、谷与 Hilbert 共识 | {s_final['thickness_um']:.4f} | {interval(s_final['statistical_95pct_interval_um'])} | {interval(s_final['recommended_interval_um'])} | {s_final['cross_angle_relative_pct']:.3f}% |
| Si | 多光束修正后的峰坐标法 | {i_final['thickness_um']:.4f} | {interval(i_final['statistical_95pct_interval_um'])} | {interval(i_final['recommended_interval_um'])} | {i_final['cross_angle_relative_pct']:.3f}% |

推荐在论文正文中报告：

- **SiC 外延层厚度：** $d_{{SiC}}={s_final['thickness_um']:.3f}\\,\\mu m$，推荐不确定区间 {interval(s_final['recommended_interval_um'])} μm；
- **Si 外延层厚度：** $d_{{Si}}={i_final['thickness_um']:.3f}\\,\\mu m$，推荐不确定区间 {interval(i_final['recommended_interval_um'])} μm。

“推荐区间”取统计 Bootstrap 区间与核心敏感性区间的并集；扩展压力测试区间分别为：

- SiC：{interval(s_final['expanded_stress_interval_um'])} μm；
- Si：{interval(i_final['expanded_stress_interval_um'])} μm。

## 3. 多光束干涉结论

### 3.1 SiC 附件 1、2

分类：`{s_mb['classification']}`。

- 峰—谷厚度中位相对差：{s_mb['peak_valley_median_relative_pct']:.3f}%；
- 二次谐波/基频中位比：{s_mb['median_h2_h1']:.4f}；
- 条纹可见度中位数：{s_mb['median_fringe_visibility']:.4f}；
- 基频修正量：{s_final['multi_beam_correction_um']:+.4f} μm。

结论：{s_mb['conclusion']}

### 3.2 Si 附件 3、4

分类：`{i_mb['classification']}`。

- 峰—谷厚度中位相对差：{i_mb['peak_valley_median_relative_pct']:.3f}%；
- 二次谐波/基频中位比：{i_mb['median_h2_h1']:.4f}；
- 条纹可见度中位数：{i_mb['median_fringe_visibility']:.4f}；
- 相对于全部方法中位数的修正量：{i_final['multi_beam_correction_um']:+.4f} μm。

结论：{i_mb['conclusion']}

## 4. 可靠性结果

### 分块 Bootstrap

光谱相邻采样点相关，因此按连续点块重采样，而不是逐点独立重采样。两组实验均完成 400 次有效重复：

- SiC 标准误：{sic['bootstrap_uncertainty']['standard_error_um']:.4f} μm；
- Si 标准误：{si['bootstrap_uncertainty']['standard_error_um']:.4f} μm。

### 核心敏感性

核心情景包括折射率 ±0.5%、入射角 ±0.2°、平滑窗口、基线阶数、包络窗口及峰值阈值：

- SiC 核心范围：{interval(sic['sensitivity_analysis']['core_range_um'])} μm；
- Si 核心范围：{interval(si['sensitivity_analysis']['core_range_um'])} μm。

### TMM 参数扫描

衬底掺杂、复折射率和吸收参数未由附件直接给出，因此 TMM 扫描只用于说明参数可辨识性：

- SiC TMM 厚度扫描范围：{interval(sic['tmm_parameter_scan']['thickness_range_um'])} μm；
- Si TMM 厚度扫描范围：{interval(si['tmm_parameter_scan']['thickness_range_um'])} μm。

该范围明显依赖衬底光学参数，故不把单个 TMM 最优值直接作为最终厚度。

## 5. 输出文件

- `outputs/tables/final_results.csv`：最终结果总表；
- `outputs/tables/*_bootstrap.csv`：400 次 Bootstrap 明细；
- `outputs/tables/*_sensitivity.csv`：敏感性情景明细；
- `outputs/tables/*_tmm_parameter_scan.csv`：TMM 有效参数扫描；
- `outputs/reports/q2_sic_summary.json`：SiC 全部数值和诊断；
- `outputs/reports/q3_si_summary.json`：Si 全部数值和诊断；
- `outputs/figures/bootstrap_*.png`：Bootstrap 分布；
- `outputs/figures/sensitivity_*.png`：敏感性条形图。

## 6. 结论边界

最终厚度依赖所采用的外延层折射率模型。Bootstrap 反映测量噪声与光谱局部相关性，不包含所有光学常数系统误差；推荐区间已额外并入核心参数敏感性。TMM 中衬底参数未被唯一识别，因此只能用于验证多光束模型的合理性和结果范围。
"""
