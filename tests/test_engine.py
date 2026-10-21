"""Unit tests for analyze_portfolio: adjusted prices + weights -> metrics."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import TRADING_DAYS_PER_YEAR, PortfolioMetrics, analyze_portfolio


def prices() -> pd.DataFrame:
    # A returns +10%, -10%, 0%; B returns 0%, +10%, -20%.
    return pd.DataFrame(
        {"A": [100.0, 110.0, 99.0, 99.0], "B": [50.0, 50.0, 55.0, 44.0]},
        index=pd.bdate_range("2024-01-02", periods=4),
    )


def test_metrics_match_hand_calculation() -> None:
    result = analyze_portfolio(prices(), [0.5, 0.5], risk_free_rate=0.04)
    daily = [0.05, 0.0, -0.10]

    assert isinstance(result, PortfolioMetrics)
    np.testing.assert_allclose(result.daily_returns, daily, atol=1e-12)
    assert result.daily_returns.index.equals(prices().index[1:])
    assert result.annualized_return == pytest.approx(np.mean(daily) * TRADING_DAYS_PER_YEAR)
    vol = np.std(daily, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert result.annualized_volatility == pytest.approx(vol)
    assert result.sharpe_ratio == pytest.approx((result.annualized_return - 0.04) / vol)
    # Wealth 1.05 -> 1.05 -> 0.945: a 10% fall from the 1.05 peak.
    assert result.max_drawdown == pytest.approx(-0.10)


def test_first_day_loss_counts_in_max_drawdown() -> None:
    falling = pd.DataFrame({"A": [100.0, 80.0, 88.0]}, index=pd.bdate_range("2024-01-02", periods=3))

    assert analyze_portfolio(falling, [1.0]).max_drawdown == pytest.approx(-0.20)


def test_constant_prices_give_zero_rates_and_nan_sharpe() -> None:
    flat = prices() * 0 + 100.0

    result = analyze_portfolio(flat, [0.5, 0.5])

    assert result.annualized_return == 0.0
    assert result.annualized_volatility == pytest.approx(0.0)
    assert np.isnan(result.sharpe_ratio)
    assert result.max_drawdown == 0.0


def test_does_not_mutate_prices() -> None:
    raw = prices()
    before = raw.copy()

    analyze_portfolio(raw, [0.5, 0.5])

    pd.testing.assert_frame_equal(raw, before)


@pytest.mark.parametrize(
    ("raw", "weights", "rate", "message"),
    [
        (prices().iloc[:2], [0.5, 0.5], 0.0, "at least 3 price dates"),
        (prices().assign(A=[100.0, np.nan, 99.0, 99.0]), [0.5, 0.5], 0.0, "missing or infinite"),
        (prices().assign(B=[50.0, 0.0, 55.0, 44.0]), [0.5, 0.5], 0.0, "positive"),
        (prices().reset_index(drop=True), [0.5, 0.5], 0.0, "indexed by date"),
        (prices(), [0.7, 0.7], 0.0, "sum to 1"),
        (prices(), [1.0], 0.0, "Expected 2"),
        (prices(), [0.5, 0.5], 4.0, "annual fraction"),
        (prices(), [0.5, 0.5], float("nan"), "finite"),
    ],
)
def test_rejects_invalid_inputs(
    raw: pd.DataFrame, weights: list[float], rate: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        analyze_portfolio(raw, weights, risk_free_rate=rate)
