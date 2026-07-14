"""Airy 模型接口。

单层 Airy 公式与本项目的单层 TMM 反射率实现等价，统一复用 tmm.py，
避免在符号约定、吸收项和偏振处理上产生两套不一致代码。
"""

from .tmm import single_layer_reflectance

__all__ = ["single_layer_reflectance"]
