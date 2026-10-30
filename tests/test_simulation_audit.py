"""Audit tests for the Monte Carlo engine: repeatability, bounds, and edge cases."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import simulate_portfolio
from risklens.analytics.simulation import MAX_PATHS, MIN_PATHS

LABELS = ["p5", "p25", "median", "p75", "p95"]


def dated(values: list[float] | np.ndarray, **kwargs: object) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=len(values), **kwargs))


def noisy(n: int = 250, seed: int = 7, scale: float = 0.02) -> pd.Series:
    return dated(np.random.default_rng(seed).normal(0.0004, scale, n))


@pytest.mark.parametrize("seed", [0, 1, 42, 2**32 - 1])
def test_same_seed_reproduces_every_output(seed: int) -> None:
    first = simulate_portfolio(noisy(), 60, 2_000, seed)
    second = simulate_portfolio(noisy(), 60, 2_000, seed)

    pd.testing.assert_frame_equal(first.percentile_paths, second.percentile_paths)
    np.testing.assert_array_equal(first.terminal_returns, second.terminal_returns)
    assert first.loss_probability == second.loss_probability


def test_numpy_and_python_int_seeds_match() -> None:
    a = simulate_portfolio(noisy(), 20, seed=5)
    b = simulate_portfolio(noisy(), 20, seed=np.int32(5))

    np.testing.assert_array_equal(a.terminal_returns, b.terminal_returns)


@pytest.mark.parametrize("scale", [0.001, 0.02, 0.08])
def test_percentiles_are_ordered_on_every_date(scale: float) -> None:
    bands = simulate_portfolio(noisy(scale=scale), 252, 5_000, 3).percentile_paths

    assert list(bands.columns) == LABELS
    assert (bands.diff(axis=1).iloc[:, 1:] >= 0).all().all()
    assert (bands > 0).all().all()  # wealth from exp() can never go negative


def test_every_path_starts_at_wealth_one_on_the_last_historical_date() -> None:
    history = noisy()
    paths = simulate_portfolio(history, 10).percentile_paths

    assert paths.index[0] == history.index[-1]
    assert (paths.iloc[0] == 1.0).all()
    future = paths.index[1:]
    assert (future > history.index[-1]).all() and future.is_monotonic_increasing
    assert (future.day_of_week < 5).all()


def test_close_stamped_history_keeps_time_of_day() -> None:
    history = pd.Series(noisy().to_numpy(), index=noisy().index + pd.Timedelta(hours=16))
    index = simulate_portfolio(history, 5).percentile_paths.index

    assert (index.hour == 16).all()


def test_timezone_aware_history_keeps_timezone() -> None:
    history = dated(noisy().to_numpy(), tz="America/New_York")
    index = simulate_portfolio(history, 5).percentile_paths.index

    assert str(index.tz) == "America/New_York"


@pytest.mark.parametrize(("daily", "loss"), [(0.0, 0.0), (0.002, 0.0), (-0.002, 1.0)])
def test_constant_history_is_deterministic(daily: float, loss: float) -> None:
    result = simulate_portfolio(dated([daily] * 30), 50, MIN_PATHS, 9)

    assert result.daily_volatility == 0.0
    assert result.loss_probability == loss
    np.testing.assert_allclose(result.terminal_returns, (1 + daily) ** 50 - 1, rtol=1e-12, atol=1e-15)
    spread = result.percentile_paths.max(axis=1) - result.percentile_paths.min(axis=1)
    assert np.allclose(spread, 0.0)


def test_tiny_real_volatility_is_not_rounded_to_zero() -> None:
    history = dated(0.001 + np.random.default_rng(1).normal(0, 1e-9, 60))

    assert simulate_portfolio(history, 5).daily_volatility > 0.0


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("drift", [-0.01, 0.0, 0.01])
def test_loss_probability_is_a_valid_share(seed: int, drift: float) -> None:
    result = simulate_portfolio(dated(drift + noisy(seed=seed).to_numpy()), 30, seed=seed)

    assert 0.0 <= result.loss_probability <= 1.0
    assert result.loss_probability == pytest.approx(np.mean(result.terminal_returns < 0))


def test_strong_drift_pushes_loss_probability_to_the_extremes() -> None:
    up = simulate_portfolio(dated(0.01 + noisy(scale=0.001).to_numpy()), 100)
    down = simulate_portfolio(dated(-0.01 + noisy(scale=0.001).to_numpy()), 100)

    assert up.loss_probability == 0.0 and down.loss_probability == 1.0


@pytest.mark.parametrize("n_returns", [0, 1])
def test_insufficient_history_is_rejected(n_returns: int) -> None:
    with pytest.raises(ValueError):
        simulate_portfolio(dated([0.01] * n_returns), 10)


def test_two_returns_is_the_minimum_history() -> None:
    result = simulate_portfolio(dated([0.01, -0.01]), 10)

    assert result.terminal_returns.shape == (MIN_PATHS,)


def test_later_returns_never_leak_into_parameters() -> None:
    full = noisy(300)
    cutoff = full.iloc[:200]
    shocked = pd.concat([cutoff, full.iloc[200:] * 50])

    a = simulate_portfolio(cutoff, 20, seed=11)
    b = simulate_portfolio(shocked.loc[: cutoff.index[-1]], 20, seed=11)

    np.testing.assert_array_equal(a.terminal_returns, b.terminal_returns)


@pytest.mark.parametrize("n_paths", [MIN_PATHS, MAX_PATHS])
def test_path_count_bounds_are_inclusive(n_paths: int) -> None:
    assert simulate_portfolio(noisy(), 1, n_paths).terminal_returns.shape == (n_paths,)


@pytest.mark.parametrize(
    "kwargs",
    [{"horizon_days": True}, {"horizon_days": 5.0}, {"n_paths": MIN_PATHS - 1}, {"seed": -1}],
)
def test_bad_settings_raise_value_error(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        simulate_portfolio(noisy(), **kwargs)
