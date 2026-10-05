"""Monte Carlo memory use: one full path buffer, bit-identical seeded output."""

import tracemalloc

import numpy as np
import pandas as pd
import pytest

from risklens.analytics.simulation import (
    MAX_HORIZON_DAYS,
    MAX_PATHS,
    PERCENTILE_LABELS,
    PERCENTILES,
    MonteCarloResult,
    _estimate_parameters,
    _future_dates,
    simulate_portfolio,
)

BYTES_PER_FLOAT = 8
# The paths buffer itself plus small per-date band arrays; the old version
# peaked at four full arrays.
MAX_PEAK_ARRAYS = 1.1


@pytest.fixture(scope="module")
def returns() -> pd.Series:
    rng = np.random.default_rng(0)
    dates = pd.bdate_range("2020-01-01", periods=1_260)
    return pd.Series(rng.normal(0.0004, 0.01, len(dates)), index=dates)


def copying_simulation(
    daily_returns: pd.Series, horizon_days: int, n_paths: int, seed: int
) -> MonteCarloResult:
    """The previous implementation: separate draw, cumsum, exp and hstack arrays."""
    mu, sigma = _estimate_parameters(daily_returns)
    dates = _future_dates(daily_returns.index[-1], horizon_days)
    daily_log_returns = np.random.default_rng(seed).normal(mu, sigma, size=(n_paths, horizon_days))
    growth = np.exp(np.cumsum(daily_log_returns, axis=1))
    wealth = np.hstack([np.ones((n_paths, 1)), growth])
    bands = np.percentile(wealth, PERCENTILES, axis=0)
    terminal_returns = wealth[:, -1] - 1.0
    return MonteCarloResult(
        percentile_paths=pd.DataFrame(bands.T, index=dates, columns=PERCENTILE_LABELS),
        terminal_returns=terminal_returns,
        loss_probability=float(np.mean(terminal_returns < 0.0)),
        daily_mean=mu,
        daily_volatility=sigma,
    )


def assert_identical(actual: MonteCarloResult, expected: MonteCarloResult) -> None:
    """Exact equality, bit for bit, not a floating-point tolerance."""
    pd.testing.assert_frame_equal(
        actual.percentile_paths, expected.percentile_paths, check_exact=True
    )
    np.testing.assert_array_equal(actual.terminal_returns, expected.terminal_returns, strict=True)
    assert actual.loss_probability == expected.loss_probability
    assert (actual.daily_mean, actual.daily_volatility) == (
        expected.daily_mean,
        expected.daily_volatility,
    )


@pytest.mark.parametrize(
    ("horizon_days", "n_paths", "seed"),
    [(1, 1_000, 0), (5, 1_000, 7), (252, 1_000, 42), (300, 2_500, 2**32 - 1)],
)
def test_same_seed_matches_the_copying_implementation_exactly(
    returns: pd.Series, horizon_days: int, n_paths: int, seed: int
) -> None:
    """In-place cumsum/exp and in-place percentiles change no output bit."""
    assert_identical(
        simulate_portfolio(returns, horizon_days, n_paths, seed),
        copying_simulation(returns, horizon_days, n_paths, seed),
    )


def test_largest_supported_run_matches_the_copying_implementation(returns: pd.Series) -> None:
    """10,000 paths x 1,260 days keeps identical bands and terminal returns."""
    assert_identical(
        simulate_portfolio(returns, MAX_HORIZON_DAYS, MAX_PATHS, 42),
        copying_simulation(returns, MAX_HORIZON_DAYS, MAX_PATHS, 42),
    )


@pytest.mark.parametrize("daily", [0.001, -0.002])
def test_zero_volatility_history_matches_the_copying_implementation(daily: float) -> None:
    """A deterministic curve is unchanged, including its exact 1.0 start row."""
    constant = pd.Series(daily, index=pd.bdate_range("2024-01-01", periods=30))
    result = simulate_portfolio(constant, 50, 1_000, 3)
    assert_identical(result, copying_simulation(constant, 50, 1_000, 3))
    assert (result.percentile_paths.iloc[0] == 1.0).all()
