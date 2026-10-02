"""Model-based one-day Value at Risk from simple daily returns.

``historical_var`` (in ``metrics``) reads the loss quantile straight from the
observed returns. This module fits two models to the same returns:

* ``normal_var``: the quantile of a normal distribution with the sample mean
  and standard deviation (parametric VaR).
* ``cornish_fisher_var``: that normal quantile adjusted for the sample's
  skewness and excess kurtosis, so lopsided or fat-tailed returns move it.

``rolling_var`` re-estimates any of the three methods each day from the
returns before it, giving the out-of-sample forecasts a backtest needs;
``kupiec_test`` checks whether a breach count is plausible, and
``var_backtest`` runs both for every method.

Every VaR here is a one-day loss as a positive fraction (0.02 == 2%), the
sign convention of ``historical_var``.
"""

import numbers

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from scipy.special import xlogy
from scipy.stats import chi2, norm

from risklens.analytics.metrics import (
    DEFAULT_VAR_CONFIDENCE,
    MIN_VOLATILITY_OBS,
    RETURN_NOISE_TOLERANCE,
    _validate_confidence,
    _validate_dated_returns,
    _validate_returns,
)

VAR_METHODS = ("historical", "normal", "cornish_fisher")
MIN_MOMENT_OBS = 4  # bias-corrected excess kurtosis needs four returns
VAR_BACKTEST_WINDOWS = (63, 126, 252)  # about a quarter, half a year, and a year
KUPIEC_SIGNIFICANCE = 0.05  # a p-value below 5% rejects the VaR model


def _skew_kurtosis(rows: np.ndarray, mean: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Bias-corrected skewness and excess kurtosis of each row, as pandas computes them.

    Rows without variation get 0 for both: there is no tail shape to adjust.
    """
    n = rows.shape[1]
    deviations = rows - mean[:, None]
    m2 = (deviations**2).mean(axis=1)
    flat = np.sqrt(m2) <= RETURN_NOISE_TOLERANCE
    m2 = np.where(flat, 1.0, m2)  # avoid dividing by zero; flat rows are reset below
    g1 = (deviations**3).mean(axis=1) / m2**1.5
    g2 = (deviations**4).mean(axis=1) / m2**2 - 3
    skew = g1 * np.sqrt(n * (n - 1)) / (n - 2)
    kurtosis = (n - 1) / ((n - 2) * (n - 3)) * ((n + 1) * g2 + 6)
    return np.where(flat, 0.0, skew), np.where(flat, 0.0, kurtosis)


def _var_rows(rows: np.ndarray, confidence: float, method: str) -> np.ndarray:
    """One-day VaR of each row of daily returns, as positive loss fractions."""
    if method == "historical":
        return -np.quantile(rows, 1 - confidence, axis=1)
    mean = rows.mean(axis=1)
    z = norm.ppf(1 - confidence)
    if method == "cornish_fisher":
        s, k = _skew_kurtosis(rows, mean)
        z = z + (z**2 - 1) * s / 6 + (z**3 - 3 * z) * k / 24 - (2 * z**3 - 5 * z) * s**2 / 36
    return -(mean + z * rows.std(axis=1, ddof=1))


def normal_var(returns: pd.Series, confidence: float = DEFAULT_VAR_CONFIDENCE) -> float:
    """One-day parametric VaR assuming normally distributed daily returns.

    ``-(mean + z * std)``: ``z`` is the standard normal quantile at
    ``1 - confidence`` (-1.645 at 95%), and the mean and sample standard
    deviation (ddof=1) come from ``returns``. Positive values are losses.

    Raises:
        ValueError: if confidence is not in (0, 1), or returns are invalid or
            fewer than 2.
    """
    _validate_confidence(confidence)
    values = _validate_returns(returns, MIN_VOLATILITY_OBS)
    return float(_var_rows(values[None, :], confidence, "normal")[0])


def cornish_fisher_var(returns: pd.Series, confidence: float = DEFAULT_VAR_CONFIDENCE) -> float:
    """One-day modified VaR: the normal quantile adjusted for skewness and kurtosis.

    The Cornish-Fisher expansion replaces ``z`` in ``normal_var`` with
    ``z + (z²-1)S/6 + (z³-3z)K/24 - (2z³-5z)S²/36``, where ``S`` is the
    sample skewness and ``K`` the sample excess kurtosis (both bias-corrected,
    as pandas computes them). Negative skew and fat tails raise the loss;
    with ``S = K = 0`` it equals ``normal_var``. The expansion is an
    approximation and can misbehave for extreme skewness or kurtosis.

    Raises:
        ValueError: if confidence is not in (0, 1), or returns are invalid or
            fewer than 4.
    """
    _validate_confidence(confidence)
    values = _validate_returns(returns, MIN_MOMENT_OBS)
    return float(_var_rows(values[None, :], confidence, "cornish_fisher")[0])


def _validate_rolling_inputs(
    returns: pd.Series, window: object, confidence: float, method: str
) -> int:
    """Return ``window`` as an int after checking every ``rolling_var`` input."""
    if method not in VAR_METHODS:
        raise ValueError(f"method must be one of {', '.join(VAR_METHODS)}; got {method!r}.")
    _validate_confidence(confidence)
    if isinstance(window, (bool, np.bool_)) or not isinstance(window, numbers.Integral):
        raise ValueError("window must be a whole number of trading days.")
    if window < MIN_MOMENT_OBS:
        raise ValueError(f"window must be at least {MIN_MOMENT_OBS} trading days; got {window}.")
    _validate_dated_returns(returns)
    if len(returns) <= window:
        raise ValueError(
            f"Need more than {window} daily returns to forecast VaR from a {window}-day "
            f"window; got {len(returns)}."
        )
    return int(window)


def rolling_var(
    returns: pd.Series,
    window: int,
    confidence: float = DEFAULT_VAR_CONFIDENCE,
    method: str = "historical",
) -> pd.Series:
    """Out-of-sample one-day VaR forecasts from the ``window`` returns before each day.

    The value on a date uses only the ``window`` returns strictly before it,
    the VaR known that morning, so a backtest never scores a forecast on the
    data that produced it. Dates without a full earlier window are left out,
    so the result starts at the ``window + 1``-th return date. ``method`` is
    one of ``VAR_METHODS``; each forecast equals ``historical_var``,
    ``normal_var``, or ``cornish_fisher_var`` on that window.

    Raises:
        ValueError: on an unknown method, a confidence outside (0, 1), a
            window that is not a whole number of at least ``MIN_MOMENT_OBS``
            days, returns that are not dated, sorted, unique, and finite, or
            no more returns than ``window``.
    """
    w = _validate_rolling_inputs(returns, window, confidence, method)
    earlier = sliding_window_view(returns.to_numpy(dtype=float)[:-1], w)
    return pd.Series(_var_rows(earlier, confidence, method), index=returns.index[w:], name="var")


def _whole_number(value: object, name: str) -> int:
    """Return ``value`` as an int, rejecting booleans and non-integers."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral):
        raise ValueError(f"{name} must be a whole number.")
    return int(value)


def kupiec_test(breaches: int, days: int, confidence: float) -> tuple[float, float]:
    """Kupiec proportion-of-failures test of a VaR breach count.

    If the VaR is right, losses exceed it on a fraction ``p = 1 - confidence``
    of days. With ``x`` breaches in ``n`` days, the likelihood ratio
    ``-2 ln[(1-p)^(n-x) p^x / ((1-x/n)^(n-x) (x/n)^x)]`` then follows a
    chi-square distribution with one degree of freedom. Returns
    ``(statistic, p_value)``. A p-value below ``KUPIEC_SIGNIFICANCE`` rejects
    the VaR: too many breaches mean it understates losses, too few that it
    overstates them.

    Raises:
        ValueError: if ``days`` is not a whole number of at least 1,
            ``breaches`` is not a whole number from 0 to ``days``, or
            confidence is not in (0, 1).
    """
    _validate_confidence(confidence)
    n, x = _whole_number(days, "days"), _whole_number(breaches, "breaches")
    if n < 1:
        raise ValueError(f"days must be at least 1; got {n}.")
    if not 0 <= x <= n:
        raise ValueError(f"breaches must be between 0 and {n}; got {x}.")
    p, rate = 1 - confidence, x / n
    log_ratio = xlogy(n - x, 1 - p) + xlogy(x, p) - xlogy(n - x, 1 - rate) - xlogy(x, rate)
    statistic = max(float(-2 * log_ratio), 0.0)  # rounding leaves about -1e-16 when rate == p
    return statistic, float(chi2.sf(statistic, df=1))


def var_backtest(
    returns: pd.Series, window: int, confidence: float = DEFAULT_VAR_CONFIDENCE
) -> pd.DataFrame:
    """Backtest every VaR method on the days after its estimation window.

    For each method in ``VAR_METHODS``, compares each day's return with that
    day's ``rolling_var`` forecast. A breach is a loss larger than the
    forecast (``return < -VaR``). Every method is tested on the same days.

    Returns:
        DataFrame indexed by method with columns ``days`` (days tested),
        ``breaches``, ``expected_breaches`` (``days * (1 - confidence)``),
        ``breach_rate`` (breaches / days), and the Kupiec ``statistic`` and
        ``p_value`` (see ``kupiec_test``).

    Raises:
        ValueError: on the same inputs as ``rolling_var``.
    """
    rows = []
    for method in VAR_METHODS:
        forecasts = rolling_var(returns, window, confidence, method)
        tested = returns.to_numpy(dtype=float)[-len(forecasts) :]
        breaches = int(np.sum(tested < -forecasts.to_numpy()))
        statistic, p_value = kupiec_test(breaches, len(forecasts), confidence)
        rows.append(
            {
                "method": method,
                "days": len(forecasts),
                "breaches": breaches,
                "expected_breaches": len(forecasts) * (1 - confidence),
                "breach_rate": breaches / len(forecasts),
                "statistic": statistic,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows).set_index("method")
