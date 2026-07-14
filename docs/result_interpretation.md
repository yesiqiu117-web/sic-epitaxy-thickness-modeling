# 结果文件阅读说明

## 最重要的三个文件

1. `outputs/reports/final_results.md`：可以直接用于论文结果部分的总报告；
2. `outputs/tables/final_results.csv`：最终数值总表；
3. `outputs/reports/all_results.json`：所有实验的机器可读汇总。

## 区间的含义

- `statistical_95pct_interval_um`：400 次连续块 Bootstrap 百分位区间；
- `core_sensitivity_interval_um`：折射率 ±0.5%、入射角和预处理变化形成的范围；
- `recommended_interval_um`：前两者的并集；
- `expanded_stress_interval_um`：更激进的折射率 ±1% 和拟合波段变化范围。

Bootstrap 区间不能替代折射率模型系统误差，因此论文中应优先报告推荐区间。

## 多光束分类

- `significant_multi_beam`：多光束会实质影响厚度，使用峰坐标修正；
- `non_sinusoidal_but_not_material`：波形并非理想余弦，但峰谷厚度仍一致，多光束修正量小；
- `double_beam_adequate`：双光束模型足够。

## TMM 表的含义

`*_tmm_parameter_scan.csv` 中不同衬底光学参数会给出不同厚度。该表用于说明参数可辨识性和模型敏感性，而不是从中挑一个最小 BIC 数值直接当作唯一真值。
