> **说明**：赛题正式题面共 3 问。为了与代码流水线和论文写作结构对应，本文将题目第三问最后一部分“判断 SiC 数据中是否存在多光束干涉并消除其影响”单独拆为**问题四**，因此采用“问题一—问题四”的四个工作包结构。

# 问题二：碳化硅外延层厚度计算与运行结果

## 1. 问题目标

根据问题一模型，对附件 1 和附件 2 的同一块 SiC 晶圆进行厚度反演：

- 附件 1：入射角 \(10^\circ\)；
- 附件 2：入射角 \(15^\circ\)；
- 输出两个角度的独立结果；
- 输出共享厚度的最终结果；
- 分析方法一致性、角度一致性、随机误差和参数敏感性。

---

## 2. 数据质量检查

四个附件原始数据均有 7469 行。删除首个异常零反射率点后，附件 1 和附件 2 各有 7468 个有效点。

| 附件 | 入射角 | 波数范围/\(\mathrm{cm}^{-1}\) | 反射率范围/% | 说明 |
|---|---:|---:|---:|---|
| 附件 1 | 10° | 400.1569–4000.1220 | 0.6361–95.3850 | 正常 |
| 附件 2 | 15° | 400.1569–4000.1220 | 0.9767–102.7394 | 约 3.508% 超过 100% |

附件 2 中超过 100% 的值没有被硬截断。程序将其视为仪器增益或归一化偏差，通过基线、包络和增益偏置处理，避免截断改变峰位。

---

## 3. 预处理

配置文件：`configs/q2_sic.yaml`，继承 `configs/base.yaml`。

### 3.1 异常点

- 删除首个零反射率点；
- Hampel 窗口：7；
- 阈值：3.5 个局部稳健标准差；
- 附件 1 检出 13 个异常点；
- 附件 2 检出 21 个异常点。

### 3.2 平滑

Savitzky–Golay 参数：

- 窗口长度：21；
- 多项式阶数：3。

### 3.3 基线和包络

反射率分解为

\[
R(\tilde\nu)=A(\tilde\nu)+B(\tilde\nu)y(\tilde\nu)+\varepsilon.
\]

基准参数：

- 基线阶数：3；
- 稳健迭代：6；
- 包络窗口：301；
- 包络多项式阶数：2。

标准化条纹为

\[
z(\tilde\nu)
=
\frac{R(\tilde\nu)-\widehat A(\tilde\nu)}
{\widehat B(\tilde\nu)}.
\]

---

## 4. 频段和折射率

主拟合频段：

\[
\boxed{
1500\sim4000\ \mathrm{cm}^{-1}
}.
\]

该区间远离 SiC 强声子共振区，更适合稳定反演基本条纹周期。

SiC 采用单声子 TO–LO 因子化介电函数：

\[
\varepsilon(\tilde\nu)
=
\varepsilon_\infty
\frac{
\tilde\nu_{LO}^2-\tilde\nu^2-i\gamma_{LO}\tilde\nu
}{
\tilde\nu_{TO}^2-\tilde\nu^2-i\gamma_{TO}\tilde\nu
}.
\]

再取

\[
\widetilde n(\tilde\nu)=\sqrt{\varepsilon(\tilde\nu)}.
\]

基准参数：

| 参数 | 数值 |
|---|---:|
| \(\varepsilon_\infty\) | 6.52 |
| \(\tilde\nu_{TO}\) | 797.7 \(\mathrm{cm}^{-1}\) |
| \(\tilde\nu_{LO}\) | 992.1 \(\mathrm{cm}^{-1}\) |
| \(\gamma\) | 4.0 \(\mathrm{cm}^{-1}\) |

---

## 5. 厚度算法

### 5.1 FFT 初值

在等间距修正波数域计算 FFT，识别基本周期 \(\Delta x\)：

\[
d_0=\frac{1}{2\Delta x}.
\]

FFT 用于确定厚度数量级和后续搜索初值，不作为唯一最终结果。

### 5.2 峰级次回归

\[
m_j=2d x_j+b+\varepsilon_j.
\]

对基频隔离后的峰坐标进行稳健回归，斜率的一半为厚度。

### 5.3 谷级次回归

与峰法相同，但使用谷坐标。峰谷一致性也用于判断多光束是否实质影响厚度。

### 5.4 Hilbert 相位

\[
\phi(x)=4\pi d x+\phi_0,
\qquad
d=\frac{1}{4\pi}\frac{d\phi}{dx}.
\]

### 5.5 最终估计器

SiC 使用

```text
fundamental_consensus
```

即对两个角度的峰、谷、Hilbert 共 6 个基频结果取中位数。FFT 作为初值和交叉检查，不进入最终中位数。

---

## 6. 单角度运行结果

| 数据 | FFT/μm | 峰级次/μm | 谷级次/μm | Hilbert/μm | Hilbert \(R^2\) |
|---|---:|---:|---:|---:|---:|
| 附件 1，10° | 7.4732 | 7.4891 | 7.4919 | 7.4897 | 0.999958 |
| 附件 2，15° | 7.4922 | 7.4634 | 7.4549 | 7.4573 | 0.999936 |

最终估计器的角度局部结果：

\[
d_{10^\circ}=7.4897\ \mu\mathrm m,
\qquad
d_{15^\circ}=7.4573\ \mu\mathrm m.
\]

双角度相对差：

\[
\boxed{
E_\theta=0.434\%
}.
\]

---

## 7. 最终厚度

峰、谷和 Hilbert 共识中位数为

\[
\boxed{
d_{\mathrm{SiC}}=7.4763\ \mu\mathrm m
}.
\]

论文正文建议保留合理有效数字：

\[
\boxed{
d_{\mathrm{SiC}}\approx7.48\ \mu\mathrm m
}.
\]

---

## 8. 模型比较

| 模型 | 厚度/μm | RMSE | BIC |
|---|---:|---:|---:|
| 双光束余弦 | 7.4192 | 0.1894 | -34383.81 |
| 三谐波代理 | 7.5407 | 0.1406 | -40420.19 |
| 当前有效参数 TMM | 7.4066 | 0.2854 | -25923.76 |

三谐波 BIC 比双光束改善约 6036.37，说明条纹并非理想单一余弦。但是否需要多光束厚度修正，还需结合峰谷分离、二次谐波和可见度，详见问题四。

当前 TMM 依赖未知衬底掺杂、吸收和复折射率，因此只作为敏感性模型，不作为最终厚度。

---

## 9. Bootstrap 统计不确定度

采用连续块 Bootstrap：

- 重复次数：400；
- 成功次数：400；
- 块长：80；
- 置信水平：95%。

结果：

| 指标 | 数值 |
|---|---:|
| 均值 | 7.4753 μm |
| 中位数 | 7.4754 μm |
| 标准误 | 0.0081 μm |
| 95% 区间 | [7.4580, 7.4919] μm |

Bootstrap 反映随机测量波动和光谱局部相关性，不覆盖全部折射率系统误差。

---

## 10. 敏感性分析

核心扰动包括：

- 折射率实部 ±0.5%；
- 入射角 ±0.2°；
- SG 窗口 11、31、41；
- 基线阶数 2、4；
- 包络窗口 201、401；
- 峰值 prominence 0.18、0.32。

核心敏感性范围：

\[
\boxed{
[7.4388,\ 7.5145]\ \mu\mathrm m
}.
\]

最主要误差来源是折射率：

- 折射率 -0.5%：7.5145 μm；
- 折射率 +0.5%：7.4388 μm。

入射角 ±0.2° 的影响不足 0.02%。

扩展压力测试范围：

\[
[7.4017,\ 7.5527]\ \mu\mathrm m.
\]

---

## 11. 推荐结果

统计区间：

\[
[7.4580,\ 7.4919]\ \mu\mathrm m.
\]

核心敏感性区间：

\[
[7.4388,\ 7.5145]\ \mu\mathrm m.
\]

推荐区间取两者并集：

\[
\boxed{
d_{\mathrm{SiC}}
=
7.4763\ \mu\mathrm m,
\qquad
d_{\mathrm{SiC}}\in[7.4388,7.5145]\ \mu\mathrm m
}.
\]

论文推荐表述：

> 碳化硅外延层厚度约为 \(7.48\,\mu\mathrm m\)，综合不确定区间为 \(7.44\sim7.51\,\mu\mathrm m\)。

---

## 12. 运行命令

```bash
python scripts/run_q2_sic.py --config configs/q2_sic.yaml
```

完整重算：

```bash
python scripts/run_all.py --recompute --quiet
```

快速读取已有结果并重建总报告：

```bash
python scripts/run_all.py --quiet
```

---

## 13. 主要输出文件

| 文件 | 内容 |
|---|---|
| `outputs/tables/q2_sic_single_methods.csv` | FFT、峰、谷、Hilbert |
| `outputs/tables/q2_sic_model_comparison.csv` | 三类模型比较 |
| `outputs/tables/q2_sic_band_stability.csv` | 分频段稳定性 |
| `outputs/tables/q2_sic_bootstrap.csv` | 400 次 Bootstrap |
| `outputs/tables/q2_sic_sensitivity.csv` | 参数敏感性 |
| `outputs/tables/q2_sic_tmm_parameter_scan.csv` | TMM 参数扫描 |
| `outputs/reports/q2_sic_summary.json` | SiC 全部结果 |
| `outputs/figures/preprocess_sic_*.png` | 预处理图 |
| `outputs/figures/fft_sic_*.png` | FFT 图 |
| `outputs/figures/hilbert_sic_*.png` | Hilbert 图 |
| `outputs/figures/bootstrap_q2_sic.png` | Bootstrap 图 |
| `outputs/figures/sensitivity_q2_sic.png` | 敏感性图 |

---

## 14. 问题二结论

1. 两角度、多方法均将厚度稳定定位在 \(7.45\sim7.49\,\mu\mathrm m\)；
2. Hilbert 相位回归 \(R^2>0.9999\)；
3. 双角度相对差仅 0.434%；
4. 主要误差来源是折射率，而非入射角或平滑窗口；
5. 最终结果：

\[
\boxed{
d_{\mathrm{SiC}}\approx7.48\ \mu\mathrm m,
\quad 7.44\sim7.51\ \mu\mathrm m
}.
\]
