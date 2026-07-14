import numpy as np
import pandas as pd

from epitaxy.diagnostics.multibeam import assess_multibeam_effect
from epitaxy.types import FitResult, ProcessedSpectrum, Spectrum


def _processed(visibility_high: bool):
    x = np.linspace(1.0, 10.0, 200)
    if visibility_high:
        y = 50.0 + 40.0 * np.sin(x)
    else:
        y = 50.0 + 2.0 * np.sin(x)
    raw = Spectrum("x", 10.0, x, y)
    return ProcessedSpectrum(raw, x, y, y, np.full_like(y, 50.0), y - 50.0,
                             np.ones_like(y), y - 50.0, np.zeros_like(y, dtype=bool))


def _fit(bic):
    return FitResult("m", 1.0, True, {"bic": bic})


def test_significant_multibeam_requires_combined_evidence():
    frame = pd.DataFrame([
        {"dataset": "a", "peak_um": 3.4, "valley_um": 3.5, "h2_h1": 0.08, "h3_h1": 0.1},
        {"dataset": "b", "peak_um": 3.4, "valley_um": 3.5, "h2_h1": 0.07, "h3_h1": 0.1},
    ])
    result = assess_multibeam_effect(frame, [_processed(True)], _fit(100.0), _fit(0.0))
    assert result["materially_significant"]
    assert result["classification"] == "significant_multi_beam"


def test_bic_alone_is_not_enough():
    frame = pd.DataFrame([
        {"dataset": "a", "peak_um": 7.5, "valley_um": 7.501, "h2_h1": 0.01, "h3_h1": 0.2},
        {"dataset": "b", "peak_um": 7.5, "valley_um": 7.499, "h2_h1": 0.02, "h3_h1": 0.2},
    ])
    result = assess_multibeam_effect(frame, [_processed(False)], _fit(100.0), _fit(0.0))
    assert not result["materially_significant"]
    assert result["non_sinusoidal_waveform"]
