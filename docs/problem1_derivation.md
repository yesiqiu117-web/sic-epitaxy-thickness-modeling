# 问题 1：双光束干涉厚度模型完整推导

## 1. 建模假设

1. 空气、外延层和衬底均为平行分层介质；
2. 问题 1 只保留外延层表面反射光和外延层—衬底界面一次反射后返回的光；
3. 外延层折射率允许随波数变化，记为 `n(ν̃)`；
4. 入射光在单个采样波数附近具有足够相干性；
5. 界面粗糙度和晶圆横向厚度变化在主模型中忽略，后续放入误差分析。

## 2. 折射角

外部入射角为 `θ0`，外延层内部折射角为 `θ1`。由斯涅尔定律

```math
n_0\sin\theta_0=n(\tilde\nu)\sin\theta_1.
```

空气中 `n0≈1`，因此

```math
n(\tilde\nu)\cos\theta_1
=\sqrt{n^2(\tilde\nu)-\sin^2\theta_0}.
```

## 3. 光程差与相位差

第二束光在外延层中完成一次往返，几何光程差为

```math
\Delta L=2d\cos\theta_1.
```

乘以折射率后，其光学程差为

```math
\operatorname{OPD}=2dn(\tilde\nu)\cos\theta_1.
```

波数为 `ν̃=1/λ`，传播相位差为

```math
\Phi(\tilde\nu)
=2\pi\tilde\nu\operatorname{OPD}+\phi_r
=4\pi d\tilde\nu n(\tilde\nu)\cos\theta_1+\phi_r,
```

其中 `φr` 为界面反射产生的附加相位。

定义修正波数

```math
x_\theta(\tilde\nu)
=\tilde\nu\sqrt{n^2(\tilde\nu)-\sin^2\theta_0},
```

则

```math
\Phi(\tilde\nu)=4\pi d x_\theta(\tilde\nu)+\phi_r.
```

## 4. 双光束反射率模型

设两束返回光的慢变强度分别为 `I1(ν̃)` 和 `I2(ν̃)`，则

```math
R(\tilde\nu)
=I_1+I_2+2\sqrt{I_1I_2}\cos\Phi+\varepsilon.
```

将慢变部分合并为基线 `A(ν̃)` 和振幅包络 `B(ν̃)`，得到用于计算的模型

```math
R(\tilde\nu)
=A(\tilde\nu)
+B(\tilde\nu)
\cos\left[4\pi d x_\theta(\tilde\nu)+\phi_0\right]
+\varepsilon(\tilde\nu).
```

## 5. 极值条件与厚度公式

同类相邻峰满足相位增加 `2π`：

```math
4\pi d(x_{m+1}-x_m)=2\pi.
```

故

```math
d=\frac{1}{2(x_{m+1}-x_m)}.
```

对多个同类极值编号 `m=0,1,...`，有

```math
m=2dx_m+b+\varepsilon_m,
```

其中截距 `b` 吸收未知绝对级次和反射附加相位，回归斜率的一半即为厚度。

## 6. 双角度共享约束

附件 1、2 或附件 3、4分别来自同一块晶圆，因此两个角度共享同一厚度 `d`，但允许各自具有不同的基线、振幅和相位：

```math
R_k(\tilde\nu)
=A_k(\tilde\nu)+B_k(\tilde\nu)
\cos\left[4\pi d x_k(\tilde\nu)+\phi_k\right]
+\varepsilon_k,
\quad k\in\{10^\circ,15^\circ\}.
```

这一共享约束是双角度联合拟合和角度一致性验证的基础。

## 7. 代码映射

| 数学内容 | 代码文件 |
|---|---|
| 折射率与修正波数 | `src/epitaxy/optics/refractive_index.py` |
| 双光束全谱拟合 | `src/epitaxy/optics/two_beam.py` |
| FFT 初值 | `src/epitaxy/estimation/fft_init.py` |
| 峰谷级次回归 | `src/epitaxy/estimation/peak_regression.py` |
| Hilbert 相位法 | `src/epitaxy/estimation/hilbert_phase.py` |
| 双角度实验流水线 | `src/epitaxy/pipeline.py` |
