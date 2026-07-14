# 剩余部分完成清单

| 任务 | 状态 | 主要文件 |
|---|---|---|
| 问题 1 双光束模型完整推导 | 已完成 | `docs/problem1_derivation.md` |
| 附件 1、2 SiC 最终厚度 | 已完成 | `outputs/reports/q2_sic_summary.json` |
| 附件 3、4 多光束判定 | 已完成 | `outputs/reports/q3_si_summary.json` |
| Si 多光束修正后厚度 | 已完成 | `src/epitaxy/estimation/final_estimator.py` |
| SiC 多光束影响复核 | 已完成 | `src/epitaxy/diagnostics/multibeam.py` |
| 400 次连续块 Bootstrap | 已完成 | `outputs/tables/*_bootstrap.csv` |
| 折射率与入射角敏感性 | 已完成 | `outputs/tables/*_sensitivity.csv` |
| 平滑、基线、包络和峰阈值消融 | 已完成 | `outputs/tables/*_sensitivity.csv` |
| 分频段稳定性 | 已完成 | `outputs/tables/*_band_stability.csv` |
| TMM 有效参数扫描 | 已完成 | `outputs/tables/*_tmm_parameter_scan.csv` |
| 最终中文报告与总表 | 已完成 | `outputs/reports/final_results.md`、`outputs/tables/final_results.csv` |
| 自动测试 | 已完成，12 项通过 | `tests/` |

## 不能由附件唯一确定的内容

题目附件未给出衬底掺杂浓度、有效质量、碰撞频率和完整复折射率，因此无法从四组反射率数据唯一辨识全部 TMM 物理参数。本项目已经通过有界参数扫描量化这一不可辨识性，并避免把某一组有效参数误写成唯一真实值。这是数据条件导致的结论边界，不是代码缺失。
