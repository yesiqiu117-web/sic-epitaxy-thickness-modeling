# 参数字典

| 配置项 | 含义 | 建议 |
|---|---|---|
| `primary_range_cm1` | 主拟合波数区间 | SiC: 1500–4000；Si: 550–3500 |
| `sg_window` | Savitzky–Golay 窗口 | 比较 11/21/31/41 |
| `baseline_degree` | 慢变基线多项式阶数 | 2–4，默认 3 |
| `peak_prominence` | 标准化条纹峰显著度 | 默认 0.25，做 ±20% 敏感性 |
| `peak_distance` | 相邻峰最小采样点数 | 依据采样率调整 |
| `thickness_bounds_um` | 厚度搜索范围 | 需结合 FFT 初值缩小 |
| `phase_starts` | 相位多起点 | 至少覆盖一个 2π 周期 |
| `fit_kappa_scale` | 是否拟合吸收尺度 | 问题 3 可开，问题 2 主模型默认关 |
| `kappa_scale_bounds` | 吸收尺度范围 | 不应过宽，避免厚度—吸收耦合 |
| `block_size` | Bootstrap 连续块长度 | 约一个或数个条纹周期 |

## 折射率配置

### 常数模型

```yaml
layer:
  model: constant
  n: 2.60
  kappa: 0.0
```

### Cauchy 模型

\[
n(\lambda)=A+\frac{B}{\lambda^2}+\frac{C}{\lambda^4}.
\]

```yaml
layer:
  model: cauchy
  A: 2.5
  B: 0.01
  C: 0.0
  kappa: 0.0
```

### Sellmeier 模型

```yaml
layer:
  model: sellmeier
  B: [B1, B2, B3]
  C: [C1, C2, C3]
  kappa: 0.0
```

### 波数多项式

令 `z=(wn-center)/scale`：

```yaml
layer:
  model: polynomial_wn
  coefficients: [c0, c1, c2]
  center: 2500.0
  scale: 1500.0
  kappa: 0.0
```

### 表格插值

CSV 至少包含 `wavenumber_cm1,n`，可选 `kappa`：

```yaml
layer:
  model: table
  path: data/refractive_index/sic.csv
```
