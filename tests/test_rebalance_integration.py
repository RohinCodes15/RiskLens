"""Rebalance frequency and trading cost reach every portfolio-level analysis."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    REBALANCE_FREQUENCIES,
    TRADING_DAYS_PER_YEAR,
    analyze_portfolio,
    annualized_return,
    benchmark_statistics,
    compare_to_benchmark,
    cumulative_wealth,
    portfolio_returns,
    rebalance_turnover,
)
from risklens.data import to_returns

WEIGHTS = [0.6, 0.4]


@pytest.fixture
def prices() -> pd.DataFrame:
    """Eighteen months of adjusted prices for two assets that drift apart."""
    rng = np.random.default_rng(7)
    index = pd.bdate_range("2023-01-02", periods=390)
    growth = np.cumprod(1 + rng.normal([0.001, -0.0002], 0.012, (390, 2)), axis=0)
    return pd.DataFrame(100 * growth, index=index, columns=["AAA", "BBB"])


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_engine_uses_the_rebalance_frequency(prices: pd.DataFrame, rebalance: str) -> None:
    result = analyze_portfolio(prices, WEIGHTS, rebalance=rebalance, cost_bps=10)
    expected = portfolio_returns(to_returns(prices), WEIGHTS, rebalance, 10)
    pd.testing.assert_series_equal(result.daily_returns, expected)
    assert result.annualized_return == pytest.approx(annualized_return(expected))


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_engine_reports_annual_turnover(prices: pd.DataFrame, rebalance: str) -> None:
    result = analyze_portfolio(prices, WEIGHTS, rebalance=rebalance)
    turnover = rebalance_turnover(to_returns(prices), WEIGHTS, rebalance)
    assert result.annual_turnover == pytest.approx(turnover.mean() * TRADING_DAYS_PER_YEAR)


def test_engine_defaults_match_the_original_daily_engine(prices: pd.DataFrame) -> None:
    result = analyze_portfolio(prices, WEIGHTS)
    expected = to_returns(prices).to_numpy() @ np.array(WEIGHTS)
    np.testing.assert_array_equal(result.daily_returns.to_numpy(), expected)


def test_costs_lower_engine_return_but_not_turnover(prices: pd.DataFrame) -> None:
    free = analyze_portfolio(prices, WEIGHTS, rebalance="monthly")
    costly = analyze_portfolio(prices, WEIGHTS, rebalance="monthly", cost_bps=50)
    assert costly.annualized_return < free.annualized_return
    assert costly.annual_turnover == free.annual_turnover > 0


def test_buy_and_hold_has_no_turnover(prices: pd.DataFrame) -> None:
    assert analyze_portfolio(prices, WEIGHTS, rebalance="never").annual_turnover == 0.0


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [({"rebalance": "weekly"}, "rebalance must be one of"), ({"cost_bps": -1}, "negative")],
)
def test_engine_rejects_bad_options(prices: pd.DataFrame, kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        analyze_portfolio(prices, WEIGHTS, **kwargs)


@pytest.fixture
def spy(prices: pd.DataFrame) -> pd.Series:
    rng = np.random.default_rng(8)
    growth = np.cumprod(1 + rng.normal(0.0004, 0.01, len(prices)))
    return pd.Series(400 * growth, index=prices.index, name="SPY")


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_benchmark_growth_uses_rebalance_and_cost(
    prices: pd.DataFrame, spy: pd.Series, rebalance: str
) -> None:
    curves = compare_to_benchmark(prices, WEIGHTS, spy, rebalance=rebalance, cost_bps=20)
    expected = cumulative_wealth(portfolio_returns(to_returns(prices), WEIGHTS, rebalance, 20))
    np.testing.assert_allclose(curves["portfolio"].iloc[1:].to_numpy(), expected.to_numpy())
    assert curves["portfolio"].iloc[0] == 1.0


def test_benchmark_statistics_use_rebalance_and_cost(prices: pd.DataFrame, spy: pd.Series) -> None:
    daily = benchmark_statistics(prices, WEIGHTS, spy)
    monthly = benchmark_statistics(prices, WEIGHTS, spy, rebalance="monthly")
    costly = benchmark_statistics(prices, WEIGHTS, spy, rebalance="monthly", cost_bps=50)
    assert monthly != daily
    assert costly.excess_return < monthly.excess_return


def test_benchmark_defaults_are_unchanged(prices: pd.DataFrame, spy: pd.Series) -> None:
    pd.testing.assert_frame_equal(
        compare_to_benchmark(prices, WEIGHTS, spy),
        compare_to_benchmark(prices, WEIGHTS, spy, rebalance="daily", cost_bps=0),
    )
