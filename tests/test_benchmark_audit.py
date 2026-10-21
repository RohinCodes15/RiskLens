"""Regression tests for benchmark statistics on low-volatility benchmarks."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import benchmark_statistics


def series_from_returns(returns: np.ndarray) -> pd.Series:
    prices = 100 * np.cumprod(np.concatenate([[1.0], 1 + returns]))
    return pd.Series(prices, index=pd.bdate_range("2024-01-02", periods=len(prices)))


def test_low_volatility_benchmark_still_gives_beta() -> None:
    rng = np.random.default_rng(3)
    bench_returns = 0.0002 + rng.normal(0, 5e-5, 60)  # daily volatility ~0.005%
    bench = series_from_returns(bench_returns)
    assets = pd.DataFrame({"A": series_from_returns(2 * bench_returns)})

    stats = benchmark_statistics(assets, [1.0], bench)

    assert stats.beta == pytest.approx(2.0, rel=1e-3)
    assert stats.correlation == pytest.approx(1.0)


def test_constant_benchmark_returns_are_rejected() -> None:
    bench = series_from_returns(np.full(30, 0.001))
    assets = pd.DataFrame({"A": series_from_returns(np.linspace(-0.01, 0.01, 30))})

    with pytest.raises(ValueError, match="constant"):
        benchmark_statistics(assets, [1.0], bench)
