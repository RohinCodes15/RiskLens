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
    _validate_dated_returns,
)

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







