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
    if np.isclose(vol, 0.0):  # constant returns leave ~1e-17 float noise, not exact 0
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
    clean = returns.dropna()
    if clean.empty:
        raise ValueError("No returns to compute VaR from.")
    return float(-np.quantile(clean, 1 - confidence))


def max_drawdown(returns: pd.Series) -> float:
    """Largest peak-to-trough decline of cumulative wealth, as a negative fraction."""
    wealth = (1 + returns).cumprod()
    # Peak starts at 1.0 (initial wealth) so a loss on day one still counts.
    drawdown = wealth / wealth.cummax().clip(lower=1.0) - 1
    return float(drawdown.min())


def risk_contributions(returns: pd.DataFrame, weights: Sequence[float]) -> pd.Series:
    """Each asset's share of annualized portfolio variance (fractions summing to 1).

    ``returns`` holds simple daily returns, one column per asset. Raises
    ValueError on NaNs, fewer than 2 rows, or zero portfolio variance.
    """
    if returns.isna().to_numpy().any():
        raise ValueError("returns contain NaN values; drop or fill them first")
    if len(returns) < 2:
        raise ValueError("need at least 2 rows of returns to estimate covariance")
    w = validate_weights(weights, returns.shape[1])
    cov = returns.cov().to_numpy() * TRADING_DAYS_PER_YEAR
    marginal = cov @ w
    port_var = float(w @ marginal)
    if port_var <= 0:
        raise ValueError("portfolio variance is zero; risk shares are undefined")
    shares = w * marginal / port_var
    return pd.Series(shares, index=returns.columns, name="risk_contribution")
