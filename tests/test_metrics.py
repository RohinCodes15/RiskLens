"""Unit tests for return-based metrics: calculations and input rejection."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    TRADING_DAYS_PER_YEAR,
    annualized_return,
    annualized_volatility,
    historical_var,
    portfolio_returns,
    risk_contributions,
    sharpe_ratio,
)

RETURNS = [0.01, -0.02, 0.03, 0.005]


def series(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=len(values)))


def test_portfolio_returns_weights_each_day() -> None:
    returns = pd.DataFrame({"A": [0.10, -0.10], "B": [0.00, 0.10]})

    result = portfolio_returns(returns, [0.6, 0.4])

    np.testing.assert_allclose(result, [0.06, -0.02])
    assert result.name == "portfolio"
    assert result.index.equals(returns.index)


@pytest.mark.parametrize(
    ("returns", "message"),
    [
        (pd.Series([0.01, 0.02]), "pandas DataFrame"),
        (pd.DataFrame({"A": []}, dtype=float), "No returns"),
        (pd.DataFrame({"A": [0.01, np.nan]}), "NaN or infinite"),
        (pd.DataFrame({"A": [0.01, np.inf]}), "NaN or infinite"),
        (pd.DataFrame({"A": [0.01, -1.5]}), "below -100%"),
        (pd.DataFrame({"A": ["x", "y"]}), "must be numbers"),
    ],
)
def test_portfolio_returns_rejects_bad_returns(returns: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        portfolio_returns(returns, [1.0])  # type: ignore[arg-type]


def test_annualized_return_and_volatility_use_252_days() -> None:
    returns = series(RETURNS)

    assert annualized_return(returns) == pytest.approx(np.mean(RETURNS) * TRADING_DAYS_PER_YEAR)
    assert annualized_volatility(returns) == pytest.approx(
        np.std(RETURNS, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    )


def test_sharpe_subtracts_annual_risk_free_rate() -> None:
    returns = series(RETURNS)
    expected = (annualized_return(returns) - 0.04) / annualized_volatility(returns)

    assert sharpe_ratio(returns, 0.04) == pytest.approx(expected)


def test_sharpe_is_nan_for_constant_returns() -> None:
    assert np.isnan(sharpe_ratio(series([0.01] * 5)))


@pytest.mark.parametrize(
    ("func", "returns", "message"),
    [
        (annualized_return, series([]), "No returns"),
        (annualized_return, [0.01], "pandas Series"),
        (annualized_return, series([0.01, np.nan]), "NaN or infinite"),
        (annualized_volatility, series([0.01]), "at least 2 daily returns"),
        (annualized_volatility, series([0.01, np.inf]), "NaN or infinite"),
        (sharpe_ratio, series([0.01]), "at least 2 daily returns"),
        (historical_var, series([0.01, np.nan]), "NaN or infinite"),
        (historical_var, series([]), "No returns"),
    ],
)
def test_metrics_reject_bad_returns(func: object, returns: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        func(returns)  # type: ignore[operator]


def test_sharpe_rejects_percent_risk_free_rate() -> None:
    with pytest.raises(ValueError, match="annual fraction"):
        sharpe_ratio(series(RETURNS), 4.0)


def test_historical_var_is_positive_loss_at_confidence() -> None:
    returns = series([-0.05, -0.02, 0.0, 0.01, 0.03])

    assert historical_var(returns, 0.95) == pytest.approx(-np.quantile(returns, 0.05))
    assert historical_var(returns, 0.95) > 0


def test_historical_var_is_negative_when_every_day_gains() -> None:
    assert historical_var(series([0.01, 0.02, 0.03])) < 0


@pytest.mark.parametrize("confidence", [0.0, 1.0, 1.5])
def test_historical_var_rejects_bad_confidence(confidence: float) -> None:
    with pytest.raises(ValueError, match="confidence"):
        historical_var(series(RETURNS), confidence)


def test_risk_contributions_sum_to_one_and_follow_columns() -> None:
    rng = np.random.default_rng(0)
    returns = pd.DataFrame(rng.normal(0, 0.01, (60, 2)), columns=["A", "B"])

    result = risk_contributions(returns, [0.7, 0.3])

    assert list(result.index) == ["A", "B"]
    assert result.sum() == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("returns", "message"),
    [
        (pd.DataFrame({"A": [0.01]}), "at least 2 rows"),
        (pd.DataFrame({"A": [0.01, np.nan, 0.02]}), "NaN or infinite"),
        (pd.DataFrame({"A": [0.01, 0.01, 0.01]}), "variance is zero"),
    ],
)
def test_risk_contributions_reject_bad_returns(returns: pd.DataFrame, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        risk_contributions(returns, [1.0])
