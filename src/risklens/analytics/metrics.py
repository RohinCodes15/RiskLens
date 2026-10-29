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
    """Annualized Sharpe ratio; ``risk_free_rate`` is an annual fraction (0.04 == 4%).

    Returns NaN when volatility is zero.
    """
    if not np.isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be a finite number.")
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


def _validate_dated_returns(returns: pd.Series) -> None:
    """Raise ValueError unless ``returns`` is a non-empty, finite, dated Series."""
    if not isinstance(returns, pd.Series):
        raise ValueError("returns must be a pandas Series.")
    if returns.empty:
        raise ValueError("No returns provided.")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise ValueError("returns must be indexed by date.")
    if not (returns.index.is_monotonic_increasing and returns.index.is_unique):
        raise ValueError("Return dates must be sorted and unique.")
    values = returns.to_numpy(dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("returns contain NaN or infinite values.")
    if np.any(values < -1):
        raise ValueError("A daily return below -100% is not possible.")


def cumulative_wealth(returns: pd.Series) -> pd.Series:
    """Growth of 1.0 invested before the first date, indexed by return date.

    ``returns`` are simple daily returns on a sorted, unique ``DatetimeIndex``.
    1.25 on a date means the investment is up 25% since the start.

    Raises:
        ValueError: if returns are empty, not dated, unsorted, contain
            NaN/inf, or contain a return below -100%.
    """
    _validate_dated_returns(returns)
    return (1 + returns.astype(float)).cumprod().rename("wealth")


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Daily drawdown of cumulative wealth, as fractions <= 0, indexed by date.

    Wealth starts at 1.0 before the first date, so a loss on day one shows as
    a drawdown. -0.25 means wealth is 25% below its peak. Input rules and
    errors match ``cumulative_wealth``.
    """
    wealth = cumulative_wealth(returns)
    # Peak starts at 1.0 (initial wealth) so a loss on day one still counts.
    drawdown = wealth / wealth.cummax().clip(lower=1.0) - 1
    return drawdown.rename("drawdown")


def max_drawdown(returns: pd.Series) -> float:
    """Largest peak-to-trough decline of cumulative wealth, as a negative fraction.

    Same input rules as ``drawdown_series``; 0.0 means no decline.
    """
    return float(drawdown_series(returns).min())


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
