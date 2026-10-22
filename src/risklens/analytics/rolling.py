"""Dated rolling risk metrics over trailing trading-day windows.

Every function takes simple daily returns (fractions) on a sorted, unique
``DatetimeIndex`` and returns a Series with exactly the same index. A window
of ``w`` covers the ``w`` most recent returns up to and including each date,
so there is no look-ahead. The first ``w - 1`` dates do not have a full
window yet and are NaN ("insufficient observations").

Conventions match ``risklens.analytics.metrics``: volatility is the sample
standard deviation (ddof=1) x sqrt(252), return is the mean daily return x
252, and the risk-free rate is an annual fraction. Applied to the last full
window, each function equals its whole-sample counterpart
(``annualized_volatility``, ``sharpe_ratio``, ``max_drawdown``) on that window.
"""

import numbers

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from risklens.analytics.metrics import (
    MIN_VOLATILITY_OBS,
    RETURN_NOISE_TOLERANCE,
    TRADING_DAYS_PER_YEAR,
    _validate_dated_returns,
)
from risklens.validation import validate_risk_free_rate

ROLLING_WINDOWS = (21, 63, 126)  # about one month, one quarter, and six months
MIN_WINDOW = MIN_VOLATILITY_OBS  # sample volatility needs two returns


def _validate_window(window: object) -> int:
    """Return ``window`` as an int if it is a whole number >= ``MIN_WINDOW``."""
    if isinstance(window, (bool, np.bool_)) or not isinstance(window, numbers.Integral):
        raise ValueError("window must be a whole number of trading days.")
    if window < MIN_WINDOW:
        raise ValueError(f"window must be at least {MIN_WINDOW} trading days; got {window}.")
    return int(window)


def _windows(returns: pd.Series, window: object) -> tuple[int, np.ndarray]:
    """Validate inputs and return ``(window, trailing windows of shape (n - w + 1, w))``.

    Raises:
        ValueError: on an invalid window, invalid or undated returns, or
            fewer returns than ``window`` (no date has a full window).
    """
    w = _validate_window(window)
    _validate_dated_returns(returns)
    if len(returns) < w:
        raise ValueError(f"Need at least {w} daily returns for a {w}-day window; got {len(returns)}.")
    return w, sliding_window_view(returns.to_numpy(dtype=float), w)


def _dated(values: np.ndarray, returns: pd.Series, window: int, name: str) -> pd.Series:
    """Place one value per full window on its last date; earlier dates are NaN."""
    out = np.full(len(returns), np.nan)
    out[window - 1 :] = values
    return pd.Series(out, index=returns.index, name=name)


def _annualized_volatility(windows: np.ndarray) -> np.ndarray:
    """Sample std x sqrt(252) per window, with float-rounding noise set to 0."""
    daily = windows.std(axis=1, ddof=1)
    daily[daily <= RETURN_NOISE_TOLERANCE] = 0.0
    return daily * np.sqrt(TRADING_DAYS_PER_YEAR)


def rolling_volatility(returns: pd.Series, window: int) -> pd.Series:
    """Annualized volatility of each trailing ``window`` of daily returns.

    A window of constant returns, up to float rounding (daily std <=
    ``RETURN_NOISE_TOLERANCE``), reports exactly 0.0.

    Raises:
        ValueError: see ``_windows``.
    """
    w, windows = _windows(returns, window)
    return _dated(_annualized_volatility(windows), returns, w, "rolling_volatility")


def rolling_sharpe(returns: pd.Series, window: int, risk_free_rate: float = 0.0) -> pd.Series:
    """Annualized Sharpe ratio of each trailing ``window`` of daily returns.

    (mean daily return x 252 - ``risk_free_rate``) / annualized volatility,
    where ``risk_free_rate`` is an annual fraction (0.04 == 4%). Like
    ``sharpe_ratio``, a window whose volatility is zero (``np.isclose(vol, 0)``)
    is NaN rather than infinite.

    Raises:
        ValueError: on an invalid rate (see ``validate_risk_free_rate``) or
            the inputs rejected by ``_windows``.
    """
    rate = validate_risk_free_rate(risk_free_rate)
    w, windows = _windows(returns, window)
    vol = _annualized_volatility(windows)
    excess = windows.mean(axis=1) * TRADING_DAYS_PER_YEAR - rate
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = np.where(np.isclose(vol, 0.0), np.nan, excess / vol)
    return _dated(sharpe, returns, w, "rolling_sharpe")




