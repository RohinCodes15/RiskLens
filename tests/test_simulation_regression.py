"""Regression tests pinning the Monte Carlo model's distribution, calendar, and bounds."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from risklens.analytics import simulate_portfolio
from risklens.analytics.simulation import PERCENTILE_LABELS, PERCENTILES

N_PATHS = 10_000


def history(values: list[float] | np.ndarray, start: str = "2024-01-02") -> pd.Series:
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)))


def noisy(n: int = 250, seed: int = 3) -> pd.Series:
    return history(np.random.default_rng(seed).normal(0.0004, 0.01, n))


@pytest.mark.parametrize("day", [21, 126, 252])
def test_percentile_bands_match_lognormal_quantiles(day: int) -> None:
    result = simulate_portfolio(noisy(), horizon_days=252, n_paths=N_PATHS)
    mu, sigma = result.daily_mean, result.daily_volatility
    band = result.percentile_paths.iloc[day]

    for q, label in zip(PERCENTILES, PERCENTILE_LABELS, strict=True):
        p = q / 100
        z = norm.ppf(p)
        expected_log_wealth = day * mu + z * sigma * np.sqrt(day)
        # Standard error of a sample quantile, in log-wealth units.
        se = np.sqrt(p * (1 - p) / N_PATHS) / norm.pdf(z) * sigma * np.sqrt(day)
        assert np.log(band[label]) == pytest.approx(expected_log_wealth, abs=5 * se)
