"""Model-based one-day Value at Risk from simple daily returns.

``historical_var`` (in ``metrics``) reads the loss quantile straight from the
observed returns. This module fits two models to the same returns:

* ``normal_var``: the quantile of a normal distribution with the sample mean
  and standard deviation (parametric VaR).
* ``cornish_fisher_var``: that normal quantile adjusted for the sample's
  skewness and excess kurtosis, so lopsided or fat-tailed returns move it.

Every VaR here is a one-day loss as a positive fraction (0.02 == 2%), the
sign convention of ``historical_var``.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

from risklens.analytics.metrics import (
    DEFAULT_VAR_CONFIDENCE,
    MIN_VOLATILITY_OBS,
    RETURN_NOISE_TOLERANCE,
    _validate_confidence,
    _validate_returns,
)

VAR_METHODS = ("historical", "normal", "cornish_fisher")
MIN_MOMENT_OBS = 4  # bias-corrected excess kurtosis needs four returns


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
