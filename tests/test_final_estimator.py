import pandas as pd

from epitaxy.estimation.final_estimator import estimate_final_thickness


def test_peak_only_uses_two_angles():
    frame = pd.DataFrame(
        [
            {"dataset": "a", "fft_um": 9.0, "peak_um": 3.4, "valley_um": 3.8, "hilbert_um": 3.7},
            {"dataset": "b", "fft_um": 9.0, "peak_um": 3.6, "valley_um": 3.9, "hilbert_um": 3.8},
        ]
    )
    result = estimate_final_thickness(frame, "peak_only")
    assert result.thickness_um == 3.5
    assert result.estimator == "peak_only"
    assert set(result.per_angle_um) == {"a", "b"}


def test_fundamental_consensus_excludes_coarse_fft():
    frame = pd.DataFrame(
        [
            {"dataset": "a", "fft_um": 20.0, "peak_um": 7.4, "valley_um": 7.5, "hilbert_um": 7.6},
            {"dataset": "b", "fft_um": 20.0, "peak_um": 7.5, "valley_um": 7.6, "hilbert_um": 7.4},
        ]
    )
    result = estimate_final_thickness(frame, "fundamental_consensus")
    assert abs(result.thickness_um - 7.5) < 1e-12
