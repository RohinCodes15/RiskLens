"""Unit tests for fat-tailed Monte Carlo draws: Student-t and bootstrap."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import kurtosis

from risklens.analytics import simulate_portfolio
from risklens.analytics.simulation import DISTRIBUTIONS


@pytest.fixture
def returns() -> pd.Series:
    """Fat-tailed history: Student-t(4) daily returns scaled to about 1%."""
    values = np.random.default_rng(12).standard_t(4, 1000) * 0.007
    return pd.Series(values, index=pd.bdate_range("2021-01-04", periods=1000))


def one_day_draws(result: object) -> np.ndarray:
    return np.log1p(result.terminal_returns)


def test_normal_stays_the_default_and_reports_no_df(returns: pd.Series) -> None:
    default = simulate_portfolio(returns, horizon_days=5, seed=1)
    normal = simulate_portfolio(returns, horizon_days=5, seed=1, distribution="normal")
    np.testing.assert_array_equal(default.terminal_returns, normal.terminal_returns)
    assert default.distribution == "normal"
    assert np.isnan(default.degrees_of_freedom)
    assert DISTRIBUTIONS == ("normal", "student_t", "bootstrap")


def test_student_t_matches_history_moments_with_fat_tails(returns: pd.Series) -> None:
    result = simulate_portfolio(
        returns, horizon_days=1, n_paths=10_000, seed=3, distribution="student_t"
    )
    log_returns = np.log1p(returns.to_numpy())
    excess = kurtosis(log_returns, fisher=True, bias=False)
    assert result.degrees_of_freedom == pytest.approx(4 + 6 / excess)
    draws = one_day_draws(result)
    assert draws.mean() == pytest.approx(result.daily_mean, abs=3e-4)
    assert draws.std(ddof=1) == pytest.approx(result.daily_volatility, rel=0.05)
    assert kurtosis(draws) > 1.0
    assert result.distribution == "student_t"
