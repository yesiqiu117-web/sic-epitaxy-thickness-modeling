# 数学模型—代码映射

| 论文内容 | 公式/任务 | 代码位置 |
|---|---|---|
| 数据读取 | Excel 前两列、排序、去重、首零点 | `src/epitaxy/io.py` |
| 异常处理 | Hampel | `src/epitaxy/preprocessing.py::hampel_filter` |
| 轻度平滑 | Savitzky–Golay | `src/epitaxy/preprocessing.py::preprocess_spectrum` |
| 慢变基线 | 稳健低阶多项式 | `src/epitaxy/preprocessing.py::robust_polynomial_baseline` |
| 折射率模型 | 常数/Cauchy/Sellmeier/表格 | `src/epitaxy/optics/refractive_index.py` |
| 修正波数 | x=ν√(n²−sin²θ) | `corrected_wavenumber` |
| FFT 初值 | f=2d，d=f/2 | `src/epitaxy/estimation/fft_init.py` |
| 峰级次回归 | m=2dx+b | `src/epitaxy/estimation/peak_regression.py` |
| Hilbert 相位 | φ=4πdx+φ0 | `src/epitaxy/estimation/hilbert_phase.py` |
| 双角度双光束 | 共享 d，角度独立相位/基线/振幅 | `src/epitaxy/optics/two_beam.py` |
| Fresnel 系数 | s/p 偏振 | `src/epitaxy/optics/fresnel.py` |
| Airy/TMM | 单层复折射率多光束反射 | `src/epitaxy/optics/tmm.py` |
| 双角度 TMM | 共享 d，角度独立标定项 | `src/epitaxy/estimation/joint_tmm.py` |
| 谐波判定 | H2/H1、H3/H1 | `src/epitaxy/diagnostics/harmonics.py` |
| 残差检验 | DW、Ljung–Box 近似 | `src/epitaxy/diagnostics/residuals.py` |
| 模型选择 | RMSE/AIC/BIC | `src/epitaxy/diagnostics/model_selection.py` |
| 分块 Bootstrap | 连续块索引与百分位区间 | `src/epitaxy/uncertainty/bootstrap.py` |
| 全流程 | 读取→预处理→估计→拟合→诊断→输出 | `src/epitaxy/pipeline.py` |
