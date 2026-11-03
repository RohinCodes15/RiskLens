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


def test_bootstrap_only_reuses_past_days(returns: pd.Series) -> None:
    result = simulate_portfolio(returns, horizon_days=1, seed=4, distribution="bootstrap")
    past = np.log1p(returns.to_numpy())
    nearest = np.abs(one_day_draws(result)[:, None] - past[None, :]).min(axis=1)
    assert nearest.max() < 1e-12  # exp then log1p rounds, so match within float noise
    assert np.isnan(result.degrees_of_freedom)


def test_bootstrap_paths_sum_resampled_days(returns: pd.Series) -> None:
    result = simulate_portfolio(returns, horizon_days=3, seed=5, distribution="bootstrap")
    rng = np.random.default_rng(5)
    days = rng.integers(0, len(returns), size=(1000, 3))  # 1,000 paths: one block
    expected = np.log1p(returns.to_numpy())[days].sum(axis=1)
    np.testing.assert_allclose(np.log1p(result.terminal_returns), expected)


def test_bootstrap_fills_every_block_including_a_partial_one(returns: pd.Series) -> None:
    result = simulate_portfolio(
        returns, horizon_days=2, n_paths=2_500, seed=8, distribution="bootstrap"
    )
    assert result.terminal_returns.shape == (2_500,)
    assert np.isfinite(result.terminal_returns).all()
    assert len(np.unique(result.terminal_returns[2_000:])) > 400  # last block was drawn


@pytest.mark.parametrize("distribution", ["student_t", "bootstrap"])
def test_fat_tailed_models_are_reproducible(returns: pd.Series, distribution: str) -> None:
    first = simulate_portfolio(returns, horizon_days=20, seed=9, distribution=distribution)
    again = simulate_portfolio(returns, horizon_days=20, seed=9, distribution=distribution)
    pd.testing.assert_frame_equal(first.percentile_paths, again.percentile_paths)


def test_fat_tails_widen_the_lower_band(returns: pd.Series) -> None:
    def worst(distribution: str) -> float:
        result = simulate_portfolio(
            returns, horizon_days=1, n_paths=10_000, seed=6, distribution=distribution
        )
        return float(np.quantile(result.terminal_returns, 0.001))

    assert worst("student_t") < worst("normal")


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_constant_history_gives_one_flat_path(distribution: str) -> None:
    flat = pd.Series(0.001, index=pd.bdate_range("2021-01-04", periods=30))
    result = simulate_portfolio(flat, horizon_days=10, seed=1, distribution=distribution)
    np.testing.assert_allclose(result.terminal_returns, 1.001**10 - 1)


def test_rejects_unknown_distribution(returns: pd.Series) -> None:
    with pytest.raises(ValueError, match="distribution must be one of"):
        simulate_portfolio(returns, distribution="cauchy")


def test_student_t_needs_fat_tails_and_four_returns() -> None:
    thin = pd.Series([0.01, -0.01] * 50, index=pd.bdate_range("2021-01-04", periods=100))
    with pytest.raises(ValueError, match="no fat tails"):
        simulate_portfolio(thin, distribution="student_t")
    short = pd.Series([0.01, -0.02, 0.005], index=pd.bdate_range("2021-01-04", periods=3))
    with pytest.raises(ValueError, match="at least 4 returns"):
        simulate_portfolio(short, distribution="student_t")
