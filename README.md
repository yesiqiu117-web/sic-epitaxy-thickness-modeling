# 碳化硅/硅外延层厚度反演

本项目对应 **2025 年全国大学生数学建模竞赛 B 题：碳化硅外延层厚度的确定**。仓库已集成附件 1—4，并实现双光束模型、修正波数、FFT 初值、峰谷级次回归、Hilbert 相位、双角度联合拟合、多光束诊断、TMM 敏感性、分块 Bootstrap 和参数敏感性分析。

## 最终结果

| 材料 | 建议报告值 | 条件 Bootstrap 95% 区间 | 推荐解释区间 |
|---|---:|---:|---:|
| SiC | **7.48 μm** | 7.458–7.492 μm | 7.44–7.51 μm |
| Si | **3.47 μm** | 3.450–3.520 μm | 3.43–3.57 μm |

- SiC：10°、15°及峰、谷、Hilbert 结果一致性较好；多光束波形特征未造成显著厚度偏差。
- Si：存在显著非正弦与峰谷分离，最终结果应表述为**基频峰位的多光束稳健估计**，不应声称 TMM 参数已经被唯一反演。

详细评估见 [`docs/final_result_assessment.md`](docs/final_result_assessment.md)。

## 完整目录说明

每个文件的用途、输入输出关系和 GitHub 提交建议见：

- [`仓库目录与文件说明.md`](仓库目录与文件说明.md)

## 运行环境

- Python 3.10+
- NumPy、Pandas、SciPy、Matplotlib、PyYAML、OpenPyXL

安装：

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

## 运行方式

快速读取已有结果并重新生成总表：

```bash
python scripts/run_all.py --quiet
```

从四个附件完整重算：

```bash
python scripts/run_all.py --recompute --quiet
```

分别运行：

```bash
python scripts/run_q2_sic.py
python scripts/run_q3_si.py
```

运行测试：

```bash
pytest -q
```

当前测试结果：

```text
12 passed
```

## 主要输出

```text
outputs/reports/final_results.md
outputs/reports/q2_sic_summary.json
outputs/reports/q3_si_summary.json
outputs/tables/final_results.csv
outputs/figures/
```

## 结论边界

Bootstrap 区间是在当前折射率、预处理、频段和基频选择固定条件下得到的统计区间，不覆盖全部光学常数和模型选择误差。题目未提供衬底完整掺杂与复折射率信息，因此 TMM 参数扫描用于敏感性说明，而不是唯一物理参数反演。
