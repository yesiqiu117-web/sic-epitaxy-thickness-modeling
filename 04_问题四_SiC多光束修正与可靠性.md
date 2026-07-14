> **说明**：赛题正式题面共 3 问。为了与代码流水线和论文写作结构对应，本文将题目第三问最后一部分“判断 SiC 数据中是否存在多光束干涉并消除其影响”单独拆为**问题四**，因此采用“问题一—问题四”的四个工作包结构。

# 问题四：SiC 多光束影响复核、修正与最终可靠性

## 1. 问题目标

赛题正式第三问最后要求：若附件 1、2 中也存在多光束干涉并影响 SiC 厚度精度，应消除其影响并给出修正结果。

本问题需要回答：

1. SiC 条纹是否具有非正弦或高次谐波结构；
2. 这些结构是否使峰位、谷位和厚度产生实质偏差；
3. 是否需要从问题二结果中进行多光束修正；
4. 修正后的最终厚度和可靠区间是多少。

---

## 2. 联合判定原则

不能只因为三谐波模型的 BIC 更好，就认定多光束已经实质影响厚度。数据点很多时，即使很小的波形差异也会造成很大的 BIC 改善。

程序联合检查：

1. 峰谷厚度相对差；
2. 二次谐波比；
3. 条纹可见度；
4. 三谐波相对双光束的 BIC 改善。

基准阈值：

| 指标 | 阈值 |
|---|---:|
| 峰谷厚度相对差 | 1.0% |
| \(H_2/H_1\) | 0.04 |
| 条纹可见度 | 0.12 |
| BIC 改善 | 10 |

只有峰谷分离、二次谐波和可见度同时达到阈值，才判定多光束对厚度具有实质影响。

---

## 3. 峰谷一致性

附件 1：

\[
d_{\mathrm{peak}}=7.4891\ \mu\mathrm m,
\qquad
d_{\mathrm{valley}}=7.4919\ \mu\mathrm m.
\]

峰谷相对差：0.0378%。

附件 2：

\[
d_{\mathrm{peak}}=7.4634\ \mu\mathrm m,
\qquad
d_{\mathrm{valley}}=7.4549\ \mu\mathrm m.
\]

峰谷相对差：0.1151%。

两附件中位数：

\[
\boxed{
E_{pv}=0.0764\%
}.
\]

远低于 1.0% 阈值。

---

## 4. 谐波和可见度

二次谐波：

| 数据 | \(H_2/H_1\) |
|---|---:|
| SiC 10° | 0.01567 |
| SiC 15° | 0.01998 |
| 中位数 | 0.01782 |

低于 0.04 阈值。

三次谐波：

| 数据 | \(H_3/H_1\) |
|---|---:|
| SiC 10° | 0.1953 |
| SiC 15° | 0.2125 |
| 中位数 | 0.2039 |

三次谐波较明显，但不能单独解释为多次内部反射，也可能来自仪器响应、复杂折射率相位、基线残差或局部吸收。

条纹可见度中位数：

\[
\boxed{
V=0.0885
}.
\]

低于 0.12 阈值。

---

## 5. BIC 结果

双光束 BIC：

\[
-34383.81.
\]

三谐波 BIC：

\[
-40420.19.
\]

改善量：

\[
\boxed{
\Delta\mathrm{BIC}=6036.37
}.
\]

BIC 说明波形显著偏离理想余弦，但峰谷差、二次谐波和可见度均未达到实质影响阈值。

最终分类：

```text
non_sinusoidal_but_not_material
```

含义是：

> SiC 条纹不是理想正弦波，但当前证据不足以说明多光束已经显著改变厚度。

---

## 6. 消除多光束影响的方法

### 6.1 基频隔离——最终采用

把条纹分解为

\[
y(x)=y_1(x)+y_2(x)+y_3(x)+\cdots.
\]

只保留 \(k=1\) 基频，再使用：

- 峰级次回归；
- 谷级次回归；
- Hilbert 相位法。

这样可以压制高次谐波对峰形的影响，同时保留由光学厚度决定的基本周期。

### 6.2 三谐波模型——波形验证

\[
y_k(x)
=
a_{0k}+a_{1k}x+
\sum_{h=1}^{3}
\left[
A_{hk}\cos(4\pi hdx)
+
B_{hk}\sin(4\pi hdx)
\right].
\]

两角度共享厚度，各自具有背景和谐波系数。它用于诊断非正弦结构，不直接作为最终厚度。

### 6.3 TMM 参数扫描——物理敏感性

扫描：

- \(n_{\mathrm{scale}}\in\{1.00,1.02,1.04\}\)；
- \(\kappa_{\mathrm{offset}}\in\{0.00,0.01,0.03\}\)。

九组均成功，厚度范围：

\[
[7.3714,\ 7.6540]\ \mu\mathrm m.
\]

最小 BIC 组合厚度为 7.4302 μm，但附件没有给出衬底掺杂、碰撞频率和完整复折射率，不能将该参数组解释为唯一真实状态。

---

## 7. 修正前后结果

全部 8 个 FFT、峰、谷、Hilbert 结果的中位数：

\[
d_{\mathrm{all}}=7.4811\ \mu\mathrm m.
\]

基频峰、谷和 Hilbert 共识：

\[
d_{\mathrm{fund}}=7.4763\ \mu\mathrm m.
\]

修正量：

\[
\boxed{
\Delta d_{\mathrm{multi}}
=
d_{\mathrm{fund}}-d_{\mathrm{all}}
=
-0.0049\ \mu\mathrm m
}.
\]

相对厚度约 0.065%。该修正量：

- 小于 Bootstrap 标准误 0.0081 μm；
- 远小于折射率 ±0.5% 造成的约 0.038 μm 变化。

因此多光束不是 SiC 最终误差的主要来源。

---

## 8. 为什么不采用全谱模型厚度

| 模型 | 厚度/μm |
|---|---:|
| 双光束全谱 | 7.4192 |
| 三谐波全谱 | 7.5407 |
| 当前有效参数 TMM | 7.4066 |
| 基频共识 | 7.4763 |

全谱模型不仅拟合基本周期，还同时承担基线、包络、局部吸收、仪器响应和未知衬底参数，因此厚度容易与波形参数耦合。

基频峰谷和相位方法对慢变背景、振幅和高次谐波更稳健，所以作为论文主结果。

---

## 9. 可靠性

### 双角度一致性

\[
d_{10^\circ}=7.4897\ \mu\mathrm m,
\qquad
d_{15^\circ}=7.4573\ \mu\mathrm m.
\]

相对差：0.434%。

### Bootstrap

- 400 次全部成功；
- 标准误：0.0081 μm；
- 95% 区间：

\[
[7.4580,\ 7.4919]\ \mu\mathrm m.
\]

### 核心敏感性

\[
[7.4388,\ 7.5145]\ \mu\mathrm m.
\]

### 扩展压力测试

\[
[7.4017,\ 7.5527]\ \mu\mathrm m.
\]

---

## 10. 最终结果

\[
\boxed{
d_{\mathrm{SiC}}=7.4763\ \mu\mathrm m
}.
\]

推荐区间：

\[
\boxed{
[7.4388,\ 7.5145]\ \mu\mathrm m
}.
\]

多光束修正量：

\[
\boxed{
\Delta d_{\mathrm{multi}}=-0.0049\ \mu\mathrm m
}.
\]

最终结论：

> 附件 1、2 的 SiC 条纹存在非正弦和高次谐波结构，但峰谷厚度差、二次谐波和条纹可见度均较低。基频隔离后的修正量仅约 \(-0.0049\,\mu\mathrm m\)，小于统计标准误和折射率系统误差，因此多光束对 SiC 厚度没有实质影响。

---

## 11. 运行命令

问题四已集成在 SiC 主流水线中：

```bash
python scripts/run_q2_sic.py --config configs/q2_sic.yaml
```

或：

```bash
python scripts/run_all.py --recompute --quiet
```

---

## 12. 主要代码文件

| 功能 | 文件 |
|---|---|
| 多光束综合判定 | `src/epitaxy/diagnostics/multibeam.py` |
| 谐波分析 | `src/epitaxy/diagnostics/harmonics.py` |
| 三谐波联合模型 | `src/epitaxy/estimation/joint_harmonic.py` |
| 最终估计器 | `src/epitaxy/estimation/final_estimator.py` |
| Airy/TMM | `src/epitaxy/optics/tmm.py` |
| TMM 联合拟合 | `src/epitaxy/estimation/joint_tmm.py` |
| Bootstrap | `src/epitaxy/uncertainty/bootstrap.py` |
| 敏感性 | `src/epitaxy/uncertainty/sensitivity.py` |
| TMM 扫描 | `src/epitaxy/uncertainty/tmm_scan.py` |

---

## 13. 主要输出文件

| 文件 | 内容 |
|---|---|
| `outputs/tables/harmonics_sic_10deg.csv` | 10°谐波 |
| `outputs/tables/harmonics_sic_15deg.csv` | 15°谐波 |
| `outputs/tables/q2_sic_model_comparison.csv` | 模型比较 |
| `outputs/tables/q2_sic_tmm_parameter_scan.csv` | TMM 扫描 |
| `outputs/tables/q2_sic_bootstrap.csv` | Bootstrap |
| `outputs/tables/q2_sic_sensitivity.csv` | 敏感性 |
| `outputs/reports/q2_sic_summary.json` | SiC 全部结果 |
| `outputs/figures/harmonic3_fit_sic_*.png` | 三谐波拟合图 |
| `outputs/figures/tmm_fit_sic_*.png` | TMM 拟合图 |
| `outputs/figures/bootstrap_q2_sic.png` | Bootstrap 图 |
| `outputs/figures/sensitivity_q2_sic.png` | 敏感性图 |

---

## 14. 论文推荐表述

> 通过峰谷厚度差、二次谐波比、条纹可见度及模型 BIC 的联合判定，SiC 光谱虽表现出非理想正弦特征，但峰谷厚度中位相对差仅为 0.076%，二次谐波比为 0.0178，可见度为 0.0885，均未达到多光束实质影响阈值。基频隔离后，厚度由 7.4811 μm 调整为 7.4763 μm，修正量仅为 -0.0049 μm。故多光束效应对 SiC 厚度计算的影响可忽略，最终报告 \(d_{\mathrm{SiC}}\approx7.48\,\mu m\)。
