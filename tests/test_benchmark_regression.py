"""Benchmark statistics for portfolios with a known exposure to the benchmark."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import TRADING_DAYS_PER_YEAR, benchmark_statistics

DATES = pd.bdate_range("2024-01-02", periods=61)
BENCH_RETURNS = np.random.default_rng(5).normal(0.0005, 0.01, len(DATES) - 1)


def prices_from(returns: np.ndarray, start: float = 100.0) -> pd.Series:
    """Adjusted closes whose simple daily returns are exactly ``returns``."""
    return pd.Series(start * np.cumprod(np.r_[1.0, 1.0 + returns]), index=DATES)


SPY = prices_from(BENCH_RETURNS, 400.0)
BENCH_VOL = np.std(BENCH_RETURNS, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
BENCH_ANNUAL = BENCH_RETURNS.mean() * TRADING_DAYS_PER_YEAR


@pytest.mark.parametrize("leverage", [2.0, -1.0])
def test_scaled_benchmark_returns_give_that_beta(leverage: float) -> None:
    assets = prices_from(leverage * BENCH_RETURNS).to_frame("A")

    result = benchmark_statistics(assets, [1.0], SPY)

    assert result.beta == pytest.approx(leverage)
    assert result.correlation == pytest.approx(np.sign(leverage))
    assert result.tracking_error == pytest.approx(abs(leverage - 1.0) * BENCH_VOL)
    assert result.excess_return == pytest.approx((leverage - 1.0) * BENCH_ANNUAL)


def test_half_benchmark_half_cash_has_beta_one_half() -> None:
    assets = pd.DataFrame({"SPY": SPY, "CASH": 100.0}, index=DATES)

    result = benchmark_statistics(assets, [0.5, 0.5], SPY)

    assert result.beta == pytest.approx(0.5)
    assert result.correlation == pytest.approx(1.0)
    assert result.tracking_error == pytest.approx(0.5 * BENCH_VOL)
    assert result.excess_return == pytest.approx(-0.5 * BENCH_ANNUAL)


def test_flat_portfolio_has_zero_beta_and_undefined_correlation() -> None:
    assets = pd.DataFrame({"CASH": 100.0}, index=DATES)

    result = benchmark_statistics(assets, [1.0], SPY)

    assert result.beta == pytest.approx(0.0, abs=1e-15)
    assert np.isnan(result.correlation)
    assert result.tracking_error == pytest.approx(BENCH_VOL)
    assert result.excess_return == pytest.approx(-BENCH_ANNUAL)


def test_benchmark_price_level_does_not_change_statistics() -> None:
    assets = prices_from(np.random.default_rng(6).normal(0.0003, 0.012, 60)).to_frame("A")

    base = benchmark_statistics(assets, [1.0], SPY)
    rescaled = benchmark_statistics(assets, [1.0], SPY * 0.1)

    assert rescaled.beta == pytest.approx(base.beta)
    assert rescaled.correlation == pytest.approx(base.correlation)
    assert rescaled.tracking_error == pytest.approx(base.tracking_error)
    assert rescaled.excess_return == pytest.approx(base.excess_return)
