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


def test_friday_history_continues_on_the_next_consecutive_weekdays() -> None:
    returns = history([0.01, -0.005, 0.002], start="2024-03-27")  # Wed to Fri Mar 29

    result = simulate_portfolio(returns, horizon_days=6)

    expected = pd.DatetimeIndex(
        ["2024-03-29", "2024-04-01", "2024-04-02", "2024-04-03", "2024-04-04", "2024-04-05"]
        + ["2024-04-08"]
    )
    pd.testing.assert_index_equal(result.percentile_paths.index, expected, check_names=False)


def test_break_even_paths_are_not_counted_as_losses() -> None:
    result = simulate_portfolio(history([0.0] * 20), horizon_days=10)

    np.testing.assert_array_equal(result.terminal_returns, 0.0)
    assert result.loss_probability == 0.0


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (
            pd.Series(
                [0.01, 0.02, 0.03], index=pd.to_datetime(["2024-01-02"] * 2 + ["2024-01-03"])
            ),
            "sorted and unique",
        ),
        (history([0.01, -1.5, 0.02]), "-100%"),
    ],
)
def test_duplicate_dates_and_worse_than_total_loss_are_rejected(
    raw: pd.Series, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        simulate_portfolio(raw)


def test_seed_above_the_32_bit_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="seed must be between"):
        simulate_portfolio(noisy(), seed=2**32)
