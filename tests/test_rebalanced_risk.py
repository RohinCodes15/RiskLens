"""Unit tests for risk shares of the rebalanced, cost-adjusted portfolio."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    COST_LABEL,
    REBALANCE_FREQUENCIES,
    portfolio_returns,
    rebalanced_risk_contributions,
    risk_contributions,
)

WEIGHTS = [0.5, 0.3, 0.2]


@pytest.fixture
def returns() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    return pd.DataFrame(
        rng.normal(0.0005, [0.02, 0.01, 0.015], (300, 3)),
        index=pd.bdate_range("2024-01-02", periods=300),
        columns=["AAPL", "MSFT", "KO"],
    )


def test_daily_without_costs_equals_the_classic_shares(returns: pd.DataFrame) -> None:
    result = rebalanced_risk_contributions(returns, WEIGHTS)
    pd.testing.assert_series_equal(result, risk_contributions(returns, WEIGHTS))


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
@pytest.mark.parametrize("cost_bps", [0.0, 25.0])
def test_shares_sum_to_one(returns: pd.DataFrame, rebalance: str, cost_bps: float) -> None:
    result = rebalanced_risk_contributions(returns, WEIGHTS, rebalance, cost_bps)
    assert result.sum() == pytest.approx(1.0)
    assert (COST_LABEL in result.index) == (cost_bps > 0)


def test_buy_and_hold_share_is_the_drifted_piece_covariance(returns: pd.DataFrame) -> None:
    """Rebuild the AAPL piece from drifting holdings by hand and compare its share."""
    result = rebalanced_risk_contributions(returns, WEIGHTS, "never", 10.0)
    net = portfolio_returns(returns, WEIGHTS, "never", 10.0)
    wealth = (1 + returns).cumprod().mul(WEIGHTS)
    held = wealth.shift(1).fillna(pd.Series(WEIGHTS, index=returns.columns))
    piece = held["AAPL"] / held.sum(axis=1) * returns["AAPL"]
    assert result["AAPL"] == pytest.approx(np.cov(piece, net)[0, 1] / net.var())


def test_buy_and_hold_has_no_trading_cost_share(returns: pd.DataFrame) -> None:
    result = rebalanced_risk_contributions(returns, WEIGHTS, "never", 50.0)
    assert result[COST_LABEL] == 0.0


def test_drift_moves_risk_toward_the_winner() -> None:
    days = pd.bdate_range("2024-01-02", periods=250)
    rng = np.random.default_rng(4)
    winner = 0.004 + rng.normal(0, 0.02, 250)
    flat = rng.normal(0, 0.02, 250)
    returns = pd.DataFrame({"WIN": winner, "FLAT": flat}, index=days)
    daily = rebalanced_risk_contributions(returns, [0.5, 0.5], "daily")
    held = rebalanced_risk_contributions(returns, [0.5, 0.5], "never")
    assert held["WIN"] > daily["WIN"]


def test_a_total_loss_leaves_nothing_held() -> None:
    returns = pd.DataFrame(
        {"BUST": [0.1, -1.0, 0.2, 0.3], "OK": [0.01, -0.02, 0.03, 0.01]},
        index=pd.bdate_range("2024-01-02", periods=4),
    )
    result = rebalanced_risk_contributions(returns, [0.5, 0.5], "never")
    assert np.isfinite(result).all()
    assert result.sum() == pytest.approx(1.0)


def test_rejects_bad_inputs(returns: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="at least 2 rows"):
        rebalanced_risk_contributions(returns.iloc[:1], WEIGHTS)
    with pytest.raises(ValueError, match="variance is zero"):
        rebalanced_risk_contributions(returns * 0, WEIGHTS)
    with pytest.raises(ValueError, match="sum to 1"):
        rebalanced_risk_contributions(returns, [0.5, 0.5, 0.5])
    with pytest.raises(ValueError, match="rebalance must be one of"):
        rebalanced_risk_contributions(returns, WEIGHTS, "weekly")
    with pytest.raises(ValueError):
        rebalanced_risk_contributions(returns, WEIGHTS, cost_bps=-1.0)
