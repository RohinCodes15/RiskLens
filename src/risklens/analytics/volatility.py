"""Volatility forecasts: RiskMetrics EWMA and GARCH(1,1), next to historical volatility.

Both models take simple daily returns (fractions) on a sorted, unique
``DatetimeIndex``. Each returns a dated volatility series whose value on date
``t`` uses returns up to and including ``t`` and forecasts day ``t + 1``, so
there is no look-ahead and the last value is the next-day forecast. Every
volatility is annualized: daily standard deviation x sqrt(252).

EWMA (RiskMetrics, zero mean):
    σ²_t = λ·σ²_{t−1} + (1 − λ)·r_t², started at σ²_0 = r_0², λ = 0.94.
    Its forecast is the same for every future day.

GARCH(1,1) on demeaned returns e_t = r_t − mean, with variance targeting:
    σ²_{t+1} = ω + α·e_t² + β·σ²_t,   ω = v̄·(1 − α − β),   σ²_0 = v̄,
where v̄ is the sample variance. α and β are fitted by maximizing the
Gaussian likelihood (SciPy SLSQP) subject to α, β ≥ 0 and α + β < 1, so the
forecast for h days ahead drifts from the next-day value back to the
long-run level v̄ at the rate (α + β) per day.

Limitations: one fit on the whole sample, Gaussian likelihood (fat tails
are not modeled), and parameters are treated as known.
"""

import numbers
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import lfilter

from risklens.analytics.metrics import (
    MIN_VOLATILITY_OBS,
    TRADING_DAYS_PER_YEAR,
    _validate_dated_returns,
)

EWMA_LAMBDA = 0.94  # RiskMetrics daily decay factor
ANNUALIZE = np.sqrt(TRADING_DAYS_PER_YEAR)


def _checked_returns(returns: pd.Series, min_obs: int) -> np.ndarray:
    """Return values of a dated, sorted, finite return Series with at least ``min_obs`` days."""
    _validate_dated_returns(returns)
    if len(returns) < min_obs:
        raise ValueError(f"Need at least {min_obs} daily returns; got {len(returns)}.")
    return returns.to_numpy(dtype=float)


def ewma_volatility(returns: pd.Series, decay: float = EWMA_LAMBDA) -> pd.Series:
    """Annualized RiskMetrics EWMA volatility; the value on date t forecasts t + 1.

    ``decay`` is λ in (0, 1); 0.94 is the RiskMetrics daily value. Returns are
    not demeaned, as in RiskMetrics.

    Raises:
        ValueError: if returns are not dated, sorted, unique, and finite with
            at least 2 values, or ``decay`` is not a number in (0, 1).
    """
    if isinstance(decay, (bool, np.bool_)) or not isinstance(decay, numbers.Real):
        raise ValueError("decay must be a number between 0 and 1 (0.94 for RiskMetrics).")
    if not 0 < decay < 1:
        raise ValueError("decay must be between 0 and 1.")
    values = _checked_returns(returns, MIN_VOLATILITY_OBS)
    variance = pd.Series(values**2).ewm(alpha=1.0 - decay, adjust=False).mean().to_numpy()
    return pd.Series(np.sqrt(variance) * ANNUALIZE, index=returns.index, name="ewma")


@dataclass(frozen=True)
class GarchFit:
    """A fitted GARCH(1,1). Volatilities are annualized fractions.

    Attributes:
        omega: daily variance intercept (fraction², not annualized).
        alpha: weight on yesterday's squared shock.
        beta: weight on yesterday's variance.
        mean: daily mean return removed before fitting.
        conditional_volatility: dated series; the value on date t forecasts t + 1.
        long_run_volatility: level the forecast reverts to, sqrt(v̄ × 252).
        log_likelihood: maximized Gaussian log-likelihood.
        observations: number of daily returns fitted.
    """

    omega: float
    alpha: float
    beta: float
    mean: float
    conditional_volatility: pd.Series
    long_run_volatility: float
    log_likelihood: float
    observations: int

    @property
    def persistence(self) -> float:
        """α + β: the share of a variance shock still present the next day."""
        return self.alpha + self.beta


def _conditional_variance(
    shocks: np.ndarray, omega: float, alpha: float, beta: float, start: float
) -> np.ndarray:
    """σ²_0..σ²_n: σ²_0 = ``start`` and σ²_t = ω + α·e²_{t−1} + β·σ²_{t−1}."""
    drive = omega + alpha * shocks**2
    rest, _ = lfilter([1.0], [1.0, -beta], drive, zi=[beta * start])
    return np.concatenate([[start], rest])


def _negative_log_likelihood(params: np.ndarray, shocks: np.ndarray, variance: float) -> float:
    """Gaussian negative log-likelihood of ``shocks`` under variance-targeted GARCH(1,1)."""
    alpha, beta = params
    omega = variance * (1.0 - alpha - beta)
    var = _conditional_variance(shocks, omega, alpha, beta, variance)[:-1]
    return 0.5 * float(np.sum(np.log(2.0 * np.pi * var) + shocks**2 / var))
