from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .types import ProcessedSpectrum


def _save(fig, path: str | Path, dpi: int = 180):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_preprocessing(spec: ProcessedSpectrum, path, dpi=180):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(spec.wavenumber_cm1, spec.reflectance, label="raw", alpha=0.55)
    ax.plot(spec.wavenumber_cm1, spec.smoothed, label="smoothed")
    ax.plot(spec.wavenumber_cm1, spec.baseline, label="baseline")
    ax.set_xlabel("Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Reflectance")
    ax.set_title(f"Preprocessing: {spec.raw.name}")
    ax.legend()
    _save(fig, path, dpi)


def plot_fft(freq, amp, f0, path, dpi=180):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(freq, amp)
    ax.axvline(f0, linestyle="--", label=f"f0={f0:.6g}")
    ax.set_xlabel("Frequency in corrected-wavenumber domain")
    ax.set_ylabel("Amplitude")
    ax.legend()
    _save(fig, path, dpi)


def plot_fit(spec: ProcessedSpectrum, fitted: np.ndarray, residual: np.ndarray, path, dpi=180, domain="normalized"):
    fig, ax = plt.subplots(figsize=(9, 5))
    observed = spec.normalized if domain == "normalized" else spec.smoothed
    ax.plot(spec.wavenumber_cm1, observed, label="observed")
    ax.plot(spec.wavenumber_cm1, fitted, label="fitted")
    ax.plot(spec.wavenumber_cm1, residual + np.mean(observed), label="residual (shifted)", alpha=0.65)
    ax.set_xlabel("Wavenumber (cm$^{-1}$)")
    ax.set_ylabel("Normalized fringe" if domain == "normalized" else "Reflectance")
    ax.set_title(spec.raw.name)
    ax.legend()
    _save(fig, path, dpi)


def plot_hilbert(result, path, dpi=180):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(result.x_uniform, result.phase, label="unwrapped phase")
    ax.plot(result.x_uniform, result.phase_fit, label="linear fit")
    ax.set_xlabel("Corrected wavenumber")
    ax.set_ylabel("Phase (rad)")
    ax.legend()
    _save(fig, path, dpi)


def plot_bootstrap_distribution(values, point_estimate, ci_low, ci_high, path, dpi=180):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(values, bins=28, alpha=0.75, edgecolor="black")
    ax.axvline(point_estimate, linestyle="-", linewidth=1.8, label=f"point={point_estimate:.4f} μm")
    ax.axvline(ci_low, linestyle="--", label=f"CI low={ci_low:.4f}")
    ax.axvline(ci_high, linestyle="--", label=f"CI high={ci_high:.4f}")
    ax.set_xlabel("Thickness (μm)")
    ax.set_ylabel("Bootstrap frequency")
    ax.legend()
    _save(fig, path, dpi)


def plot_sensitivity(frame, path, dpi=180):
    data = frame.loc[frame["success"] & (frame["scenario"] != "baseline")].copy()
    data = data.sort_values("relative_change_pct")
    fig_height = max(5.0, 0.32 * len(data) + 1.8)
    fig, ax = plt.subplots(figsize=(9, fig_height))
    ax.barh(data["scenario"], data["relative_change_pct"])
    ax.axvline(0.0, linewidth=1.0)
    ax.set_xlabel("Relative thickness change (%)")
    ax.set_ylabel("Sensitivity scenario")
    ax.set_title("One-factor-at-a-time sensitivity")
    _save(fig, path, dpi)
