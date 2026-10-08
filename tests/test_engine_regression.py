"""analyze_portfolio agrees with single-asset metrics and ignores price levels."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    PortfolioMetrics,
    analyze_portfolio,
    annualized_return,
    annualized_volatility,
    max_drawdown,
    sharpe_ratio,
)
from risklens.data import to_returns


def two_assets() -> pd.DataFrame:
    rng = np.random.default_rng(9)
    returns = rng.normal([4e-4, 2e-4], [0.012, 0.007], size=(250, 2))
    return pd.DataFrame(
        100 * np.cumprod(1 + returns, axis=0),
        index=pd.bdate_range("2024-01-02", periods=250),
        columns=["A", "B"],
    )


def assert_same_metrics(actual: PortfolioMetrics, expected: PortfolioMetrics) -> None:
    pd.testing.assert_series_equal(actual.daily_returns, expected.daily_returns)
    assert actual.annualized_return == pytest.approx(expected.annualized_return)
    assert actual.annualized_volatility == pytest.approx(expected.annualized_volatility)
    assert actual.sharpe_ratio == pytest.approx(expected.sharpe_ratio)
    assert actual.max_drawdown == pytest.approx(expected.max_drawdown)


def test_all_weight_on_one_asset_gives_that_assets_metrics() -> None:
    prices = two_assets()
    own = to_returns(prices["B"])

    result = analyze_portfolio(prices, [0.0, 1.0], risk_free_rate=0.02)

    assert result.annualized_return == pytest.approx(annualized_return(own))
    assert result.annualized_volatility == pytest.approx(annualized_volatility(own))
    assert result.sharpe_ratio == pytest.approx(sharpe_ratio(own, 0.02))
    assert result.max_drawdown == pytest.approx(max_drawdown(own))


def test_splitting_an_asset_across_identical_columns_changes_nothing() -> None:
    prices = two_assets()
    split = prices.assign(A2=prices["A"])

    assert_same_metrics(
        analyze_portfolio(split, [0.3, 0.4, 0.3]), analyze_portfolio(prices, [0.6, 0.4])
    )
