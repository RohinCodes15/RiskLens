"""Information ratio and up/down capture against the benchmark."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import benchmark_statistics

DAYS = 252
PORTFOLIO = [0.02, -0.01, 0.03, -0.03]
BENCHMARK = [0.01, -0.02, 0.03, -0.01]


def prices_from(returns: list[float]) -> pd.Series:
    values = 100 * np.cumprod([1.0, *(1 + np.asarray(returns))])
    return pd.Series(values, index=pd.bdate_range("2026-01-05", periods=len(values)))


def statistics(portfolio: list[float], benchmark: list[float]) -> object:
    return benchmark_statistics(
        prices_from(portfolio).to_frame("A"), [1.0], prices_from(benchmark).rename("SPY")
    )


def test_information_ratio_is_annual_excess_return_per_unit_of_tracking_error() -> None:
    active = np.subtract(PORTFOLIO, BENCHMARK)
    expected = active.mean() * DAYS / (active.std(ddof=1) * np.sqrt(DAYS))
    result = statistics(PORTFOLIO, BENCHMARK)
    assert result.information_ratio == pytest.approx(expected)
    assert result.information_ratio == pytest.approx(result.excess_return / result.tracking_error)


def test_information_ratio_is_nan_when_the_portfolio_is_the_benchmark() -> None:
    assert np.isnan(statistics(BENCHMARK, BENCHMARK).information_ratio)


def geometric_mean(returns: list[float]) -> float:
    return float(np.prod(1 + np.asarray(returns)) ** (1 / len(returns)) - 1)


def test_capture_compares_geometric_mean_returns_on_up_and_down_days() -> None:
    result = statistics(PORTFOLIO, BENCHMARK)
    # The benchmark rose on days 1 and 3 and fell on days 2 and 4.
    assert result.upside_capture == pytest.approx(
        geometric_mean([0.02, 0.03]) / geometric_mean([0.01, 0.03])
    )
    assert result.downside_capture == pytest.approx(
        geometric_mean([-0.01, -0.03]) / geometric_mean([-0.02, -0.01])
    )


def test_tracking_the_benchmark_captures_exactly_all_of_it() -> None:
    result = statistics(BENCHMARK, BENCHMARK)
    assert result.upside_capture == pytest.approx(1.0)
    assert result.downside_capture == pytest.approx(1.0)


def test_gaining_on_down_days_gives_negative_downside_capture() -> None:
    assert statistics([0.01, 0.01, 0.02, 0.01], BENCHMARK).downside_capture < 0


def test_capture_is_nan_without_up_or_down_days_and_ignores_flat_days() -> None:
    rising = statistics(PORTFOLIO, [0.01, 0.02, 0.0, 0.01])
    assert np.isnan(rising.downside_capture)
    assert rising.upside_capture == pytest.approx(
        geometric_mean([0.02, -0.01, -0.03]) / geometric_mean([0.01, 0.02, 0.01])
    )
    assert np.isnan(statistics(PORTFOLIO, [-0.01, -0.02, 0.0, -0.01]).upside_capture)
