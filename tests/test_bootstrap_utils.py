import numpy as np

from epitaxy.uncertainty.bootstrap import block_bootstrap_indices, percentile_interval


def test_block_bootstrap_indices_length_and_bounds():
    rng = np.random.default_rng(1)
    idx = block_bootstrap_indices(101, 12, rng)
    assert len(idx) == 101
    assert idx.min() >= 0
    assert idx.max() < 101


def test_percentile_interval():
    lo, hi = percentile_interval(np.arange(100.0), 0.90)
    assert lo < hi
    assert 4.0 < lo < 6.0
    assert 93.0 < hi < 95.0
