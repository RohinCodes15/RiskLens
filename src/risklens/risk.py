"""Portfolio risk metrics computed from simple daily returns.

All inputs are daily returns as fractions (0.01 == 1%). Annualized figures
assume ``TRADING_DAYS_PER_YEAR`` trading days.
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from risklens.validation import validate_weights

TRADING_DAYS_PER_YEAR = 252
DEFAULT_VAR_CONFIDENCE = 0.95


def portfolio_returns(returns: pd.DataFrame, weights: Sequence[float]) -> pd.Series:
    """Daily portfolio returns for a fixed-weight (daily rebalanced) portfolio."""
    w = validate_weights(weights, returns.shape[1])
    return pd.Series(returns.to_numpy() @ w, index=returns.index, name="portfolio")


def annualized_return(returns: pd.Series) -> float:
    """Arithmetic mean daily return scaled to one year."""
    return float(returns.mean() * TRADING_DAYS_PER_YEAR)


def annualized_volatility(returns: pd.Series) -> float:
    """Sample standard deviation of daily returns scaled by sqrt(252)."""
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio; ``risk_free_rate`` is an annual fraction.

    Returns NaN when volatility is zero.
    """
    vol = annualized_volatility(returns)
    if vol == 0:
        return float("nan")
    return (annualized_return(returns) - risk_free_rate) / vol


def historical_var(
    returns: pd.Series, confidence: float = DEFAULT_VAR_CONFIDENCE
) -> float:
    """One-day historical Value at Risk, reported as a positive loss fraction.

    A result of 0.02 means: on (1 - confidence) of days, the loss was at
    least 2%.
    """
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")
    return float(-np.quantile(returns.dropna(), 1 - confidence))


def max_drawdown(returns: pd.Series) -> float:
    """Largest peak-to-trough decline of cumulative wealth, as a negative fraction."""
    wealth = (1 + returns).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    return float(drawdown.min())
