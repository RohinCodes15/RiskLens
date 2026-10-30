"""Unit tests for the Monte Carlo portfolio simulation."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import MonteCarloResult, simulate_portfolio

LABELS = ["p5", "p25", "median", "p75", "p95"]


def history(values: list[float] | np.ndarray) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=len(values)), name="portfolio")


@pytest.fixture
def returns() -> pd.Series:
    return history(np.random.default_rng(7).normal(0.0005, 0.01, 120))


def test_paths_start_at_one_on_last_date_and_move_forward(returns: pd.Series) -> None:
    result = simulate_portfolio(returns, horizon_days=10, n_paths=1_000)

    paths = result.percentile_paths
    assert isinstance(result, MonteCarloResult)
    assert list(paths.columns) == LABELS
    assert len(paths) == 11
    assert (paths.iloc[0] == 1.0).all()
    assert paths.index[0] == returns.index[-1]
    assert (paths.index[1:] > returns.index[-1]).all()
    assert paths.index.is_monotonic_increasing and paths.index.is_unique
    assert (paths.index[1:].day_of_week < 5).all()


def test_same_seed_reproduces_and_new_seed_differs(returns: pd.Series) -> None:
    first = simulate_portfolio(returns, horizon_days=20, seed=1)
    again = simulate_portfolio(returns, horizon_days=20, seed=1)
    other = simulate_portfolio(returns, horizon_days=20, seed=2)

    pd.testing.assert_frame_equal(first.percentile_paths, again.percentile_paths)
    np.testing.assert_array_equal(first.terminal_returns, again.terminal_returns)
    assert not np.array_equal(first.terminal_returns, other.terminal_returns)


def test_percentiles_are_ordered_and_terminal_stats_agree(returns: pd.Series) -> None:
    result = simulate_portfolio(returns, horizon_days=30, n_paths=2_000)

    assert (result.percentile_paths.diff(axis=1).iloc[:, 1:] >= 0).all().all()
    assert result.terminal_returns.shape == (2_000,)
    assert result.loss_probability == pytest.approx(np.mean(result.terminal_returns < 0))
    assert 0.0 <= result.loss_probability <= 1.0
    final = result.percentile_paths.iloc[-1]
    assert final["median"] == pytest.approx(np.median(1.0 + result.terminal_returns))
    assert final["p5"] == pytest.approx(np.percentile(1.0 + result.terminal_returns, 5))


def test_terminal_log_wealth_matches_model_moments(returns: pd.Series) -> None:
    horizon, paths = 60, 10_000
    result = simulate_portfolio(returns, horizon_days=horizon, n_paths=paths)

    log_wealth = np.log1p(result.terminal_returns)
    expected_sd = result.daily_volatility * np.sqrt(horizon)
    # Four standard errors keeps the seeded check meaningful but not brittle.
    assert log_wealth.mean() == pytest.approx(result.daily_mean * horizon, abs=4 * expected_sd / np.sqrt(paths))
    assert log_wealth.std(ddof=1) == pytest.approx(expected_sd, rel=0.05)


@pytest.mark.parametrize(("daily", "loss"), [(0.001, 0.0), (-0.001, 1.0)])
def test_zero_volatility_gives_one_deterministic_curve(daily: float, loss: float) -> None:
    result = simulate_portfolio(history([daily] * 30), horizon_days=5, n_paths=1_000)

    curve = (1.0 + daily) ** np.arange(6)
    assert result.daily_volatility == 0.0
    for label in LABELS:
        np.testing.assert_allclose(result.percentile_paths[label], curve)
    np.testing.assert_allclose(result.terminal_returns, curve[-1] - 1.0)
    assert result.loss_probability == loss


def test_uses_only_history_before_start(returns: pd.Series) -> None:
    past = returns.iloc[:60]

    result = simulate_portfolio(past, horizon_days=5)

    assert result.daily_mean == pytest.approx(np.log1p(past).mean())
    assert result.daily_volatility == pytest.approx(np.log1p(past).std(ddof=1))
    assert result.percentile_paths.index[0] == past.index[-1]


def test_does_not_mutate_returns(returns: pd.Series) -> None:
    before = returns.copy()

    simulate_portfolio(returns, horizon_days=5)

    pd.testing.assert_series_equal(returns, before)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ([0.01, 0.02], "pandas Series"),
        (history([0.01]), "at least 2"),
        (history([0.01, np.nan, 0.02]), "NaN or infinite"),
        (history([0.01, -1.0, 0.02]), "-100%"),
        (pd.Series([0.01, 0.02, 0.03]), "indexed by date"),
        (history([0.01, 0.02, 0.03]).iloc[::-1], "sorted and unique"),
    ],
)
def test_rejects_bad_returns(raw: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        simulate_portfolio(raw)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"horizon_days": 0}, "horizon_days must be between"),
        ({"horizon_days": 1_261}, "horizon_days must be between"),
        ({"horizon_days": 2.5}, "horizon_days must be a whole number"),
        ({"horizon_days": True}, "horizon_days must be a whole number"),
        ({"n_paths": 999}, "n_paths must be between"),
        ({"n_paths": 10_001}, "n_paths must be between"),
        ({"seed": -1}, "seed must be between"),
        ({"seed": None}, "seed must be a whole number"),
    ],
)
def test_rejects_bad_settings(returns: pd.Series, kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        simulate_portfolio(returns, **kwargs)  # type: ignore[arg-type]
