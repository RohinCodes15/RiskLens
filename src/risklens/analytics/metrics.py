"""Portfolio risk metrics computed from simple daily returns.

All inputs are daily returns as fractions (0.01 == 1%). Annualized figures
assume ``TRADING_DAYS_PER_YEAR`` trading days.
"""

import numbers
from collections.abc import Sequence

import numpy as np
import pandas as pd

from risklens.validation import validate_risk_free_rate, validate_weights

TRADING_DAYS_PER_YEAR = 252
DEFAULT_VAR_CONFIDENCE = 0.95
VAR_CONFIDENCE_LEVELS = (0.95, 0.99)
MIN_VOLATILITY_OBS = 2  # sample std (ddof=1) needs two returns
# A daily-return standard deviation at or below this is float rounding (returns
# from constant-growth prices carry ~1e-16 noise), not real volatility.
RETURN_NOISE_TOLERANCE = 1e-12


def _as_float_values(returns: pd.Series | pd.DataFrame) -> np.ndarray:
    """Return ``returns`` as floats, rejecting text, NaN/inf, and < -100% days."""
    try:
        values = returns.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("returns must be numbers.") from exc
    if not np.all(np.isfinite(values)):
        raise ValueError("returns contain NaN or infinite values.")
    if np.any(values < -1):
        raise ValueError("A daily return below -100% is not possible.")
    return values


def _validate_returns(returns: pd.Series, min_obs: int = 1) -> np.ndarray:
    """Raise ValueError unless ``returns`` is a finite Series of ``min_obs``+ values."""
    if not isinstance(returns, pd.Series):
        raise ValueError("returns must be a pandas Series.")
    if returns.empty:
        raise ValueError("No returns provided.")
    if len(returns) < min_obs:
        raise ValueError(f"Need at least {min_obs} daily returns; got {len(returns)}.")
    return _as_float_values(returns)


def portfolio_returns(returns: pd.DataFrame, weights: Sequence[float]) -> pd.Series:
    """Daily portfolio returns for a fixed-weight (daily rebalanced) portfolio.

    Raises:
        ValueError: if ``returns`` is not a non-empty DataFrame of finite
            returns >= -100%, or the weights are invalid.
    """
    if not isinstance(returns, pd.DataFrame):
        raise ValueError("returns must be a pandas DataFrame.")
    if returns.empty:
        raise ValueError("No returns provided.")
    w = validate_weights(weights, returns.shape[1])
    values = _as_float_values(returns)
    return pd.Series(values @ w, index=returns.index, name="portfolio")


def annualized_return(returns: pd.Series) -> float:
    """Arithmetic mean daily return scaled to one year.

    Raises:
        ValueError: if returns are empty, non-numeric, or NaN/inf.
    """
    return float(_validate_returns(returns).mean() * TRADING_DAYS_PER_YEAR)


def annualized_volatility(returns: pd.Series) -> float:
    """Sample standard deviation of daily returns scaled by sqrt(252).

    Raises:
        ValueError: if fewer than 2 returns, non-numeric, or NaN/inf.
    """
    values = _validate_returns(returns, MIN_VOLATILITY_OBS)
    return float(values.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio; ``risk_free_rate`` is an annual fraction (0.04 == 4%).

    Returns NaN when volatility is zero. Raises ValueError for an invalid
    rate (see ``validate_risk_free_rate``) or invalid returns.
    """
    rate = validate_risk_free_rate(risk_free_rate)
    vol = annualized_volatility(returns)
    if np.isclose(vol, 0.0):  # constant returns leave ~1e-17 float noise, not exact 0
        return float("nan")
    return (annualized_return(returns) - rate) / vol


def historical_var(
    returns: pd.Series, confidence: float = DEFAULT_VAR_CONFIDENCE
) -> float:
    """One-day historical Value at Risk, reported as a positive loss fraction.

    A result of 0.02 means: on (1 - confidence) of days, the loss was at
    least 2%. A negative result means even the worst days were gains.
    Uses linear interpolation between observed returns.

    Raises:
        ValueError: if confidence is not in (0, 1) or returns are invalid.
    """
    _validate_confidence(confidence)
    values = _validate_returns(returns)
    return float(-np.quantile(values, 1 - confidence))


def _validate_confidence(confidence: float) -> None:
    """Raise ValueError unless ``confidence`` is a fraction strictly inside (0, 1)."""
    if isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence, numbers.Real):
        raise ValueError("confidence must be a number between 0 and 1 (0.95 for 95%).")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")


def historical_cvar(
    returns: pd.Series, confidence: float = DEFAULT_VAR_CONFIDENCE
) -> float:
    """One-day historical CVaR (Expected Shortfall), as a positive loss fraction.

    Tail method: the tail is every observed daily return at or below the
    ``1 - confidence`` quantile (the same linearly interpolated quantile as
    ``historical_var``). CVaR is minus the mean of that tail, so 0.03 means
    the average loss on the worst days was 3%. The tail always contains at
    least the worst return, and the result is never below ``historical_var``.

    Raises:
        ValueError: if confidence is not in (0, 1) or returns are invalid.
    """
    _validate_confidence(confidence)
    values = _validate_returns(returns)
    threshold = np.quantile(values, 1 - confidence)
    tail = values[values <= threshold]
    var = -float(threshold)
    cvar = -float(tail.mean())
    return max(cvar, var)


def tail_risk_summary(
    returns: pd.Series, confidence_levels: Sequence[float] = VAR_CONFIDENCE_LEVELS
) -> pd.DataFrame:
    """Historical VaR and CVaR for each confidence level, indexed by confidence.

    Columns: ``var`` and ``cvar`` (positive one-day loss fractions) and
    ``sufficient_sample``. That flag is False when there are fewer returns
    than ``1 / (1 - confidence)`` (e.g. under 100 for 99%): the tail is then
    thinner than one full observation, so both figures fall back to the worst day.

    Raises:
        ValueError: if a confidence is not in (0, 1) or returns are invalid.
    """
    values = _validate_returns(returns)
    rows = []
    for confidence in confidence_levels:
        expected_tail_size = len(values) * (1 - confidence)
        rows.append(
            {
                "confidence": confidence,
                "var": historical_var(returns, confidence),
                "cvar": historical_cvar(returns, confidence),
                "sufficient_sample": expected_tail_size >= 1 - RETURN_NOISE_TOLERANCE,
            }
        )
    columns = ["confidence", "var", "cvar", "sufficient_sample"]
    return pd.DataFrame(rows, columns=columns).set_index("confidence")


def _validate_dated_returns(returns: pd.Series) -> None:
    """Raise ValueError unless ``returns`` is a non-empty, finite, dated Series."""
    _validate_returns(returns)
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise ValueError("returns must be indexed by date.")
    if not (returns.index.is_monotonic_increasing and returns.index.is_unique):
        raise ValueError("Return dates must be sorted and unique.")


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
    ValueError on NaN/inf, fewer than 2 rows, or zero portfolio variance.
    """
    if not isinstance(returns, pd.DataFrame):
        raise ValueError("returns must be a pandas DataFrame.")
    if len(returns) < MIN_VOLATILITY_OBS:
        raise ValueError("need at least 2 rows of returns to estimate covariance")
    w = validate_weights(weights, returns.shape[1])
    _as_float_values(returns)
    cov = returns.cov().to_numpy() * TRADING_DAYS_PER_YEAR
    marginal = cov @ w
    port_var = float(w @ marginal)
    if port_var <= 0:
        raise ValueError("portfolio variance is zero; risk shares are undefined")
    shares = w * marginal / port_var
    return pd.Series(shares, index=returns.columns, name="risk_contribution")
