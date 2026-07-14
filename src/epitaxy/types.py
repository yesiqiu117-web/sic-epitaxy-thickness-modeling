from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Spectrum:
    name: str
    angle_deg: float
    wavenumber_cm1: np.ndarray
    reflectance: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedSpectrum:
    raw: Spectrum
    wavenumber_cm1: np.ndarray
    reflectance: np.ndarray
    smoothed: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    envelope: np.ndarray
    normalized: np.ndarray
    outlier_mask: np.ndarray


@dataclass
class FitResult:
    method: str
    thickness_um: float
    success: bool
    metrics: dict[str, float]
    parameters: dict[str, Any] = field(default_factory=dict)
    fitted: dict[str, np.ndarray] = field(default_factory=dict)
    residuals: dict[str, np.ndarray] = field(default_factory=dict)
