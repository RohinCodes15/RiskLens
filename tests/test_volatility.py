"""Unit tests for EWMA and GARCH(1,1) volatility forecasts."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    EWMA_LAMBDA,
    MAX_FORECAST_DAYS,
    MIN_GARCH_OBS,
    ewma_volatility,
    fit_garch,
    garch_forecast,
    horizon_volatility,
)

ANNUALIZE = np.sqrt(252)


def dated(values: np.ndarray) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2015-01-02", periods=len(values)))


@pytest.fixture(scope="module")
def garch_returns() -> pd.Series:
    """5,000 days simulated from GARCH(1,1) with ω = 2e-6, α = 0.08, β = 0.90."""
    rng = np.random.default_rng(0)
    omega, alpha, beta = 2e-6, 0.08, 0.90
    values, variance = np.empty(5000), omega / (1 - alpha - beta)
    for t in range(len(values)):
        values[t] = np.sqrt(variance) * rng.standard_normal()
        variance = omega + alpha * values[t] ** 2 + beta * variance
    return dated(values)


# --- EWMA ------------------------------------------------------------------------------


def test_ewma_matches_the_riskmetrics_recursion() -> None:
    returns = dated(np.random.default_rng(1).normal(0, 0.01, 300))
    variance = np.empty(300)
    variance[0] = returns.iloc[0] ** 2
    for t in range(1, 300):
        variance[t] = EWMA_LAMBDA * variance[t - 1] + (1 - EWMA_LAMBDA) * returns.iloc[t] ** 2
    result = ewma_volatility(returns)
    np.testing.assert_allclose(result.to_numpy(), np.sqrt(variance) * ANNUALIZE)
    assert result.index.equals(returns.index)
    assert result.name == "ewma"


def test_ewma_reacts_to_a_volatility_jump_and_decays() -> None:
    calm, wild = np.full(200, 0.005), np.full(5, 0.05)
    result = ewma_volatility(dated(np.concatenate([calm, wild, calm])))
    assert result.iloc[204] > 3 * result.iloc[199]
    assert result.iloc[-1] < result.iloc[204]


def test_ewma_uses_no_future_returns() -> None:
    returns = dated(np.random.default_rng(2).normal(0, 0.01, 100))
    full = ewma_volatility(returns)
    pd.testing.assert_series_equal(ewma_volatility(returns.iloc[:60]), full.iloc[:60])


def test_ewma_decay_can_be_changed() -> None:
    returns = dated(np.array([0.01, -0.02, 0.03]))
    result = ewma_volatility(returns, decay=0.5)
    expected = np.sqrt([1e-4, 0.5 * 1e-4 + 0.5 * 4e-4, 0.5 * 2.5e-4 + 0.5 * 9e-4]) * ANNUALIZE
    np.testing.assert_allclose(result.to_numpy(), expected)


@pytest.mark.parametrize(
    ("decay", "message"),
    [(0.0, "between 0 and 1"), (1.0, "between 0 and 1"), (True, "a number"), ("0.9", "a number")],
)
def test_ewma_rejects_bad_decay(decay: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ewma_volatility(dated(np.array([0.01, 0.02])), decay=decay)  # type: ignore[arg-type]


def test_ewma_rejects_bad_returns() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        ewma_volatility(dated(np.array([0.01])))
    with pytest.raises(ValueError, match="indexed by date"):
        ewma_volatility(pd.Series([0.01, 0.02]))
    with pytest.raises(ValueError):
        ewma_volatility(dated(np.array([0.01, np.nan])))


# --- GARCH -----------------------------------------------------------------------------


def test_garch_recovers_known_parameters(garch_returns: pd.Series) -> None:
    fit = fit_garch(garch_returns)
    assert fit.alpha == pytest.approx(0.08, abs=0.02)
    assert fit.beta == pytest.approx(0.90, abs=0.03)
    assert fit.persistence < 1
    assert fit.omega == pytest.approx(garch_returns.var() * (1 - fit.persistence), rel=1e-6)
    assert fit.long_run_volatility == pytest.approx(garch_returns.std() * ANNUALIZE)
    assert fit.observations == 5000
    assert fit.conditional_volatility.index.equals(garch_returns.index)


def test_garch_conditional_volatility_follows_the_recursion(garch_returns: pd.Series) -> None:
    fit = fit_garch(garch_returns)
    shocks = garch_returns.to_numpy() - fit.mean
    variance = garch_returns.var()
    for t in range(5):
        variance = fit.omega + fit.alpha * shocks[t] ** 2 + fit.beta * variance
        assert fit.conditional_volatility.iloc[t] == pytest.approx(np.sqrt(variance) * ANNUALIZE)


def test_garch_log_likelihood_beats_constant_variance(garch_returns: pd.Series) -> None:
    fit = fit_garch(garch_returns)
    shocks = garch_returns.to_numpy() - fit.mean
    variance = shocks.var(ddof=1)
    constant = -0.5 * np.sum(np.log(2 * np.pi * variance) + shocks**2 / variance)
    assert fit.log_likelihood > constant


def test_forecast_starts_at_next_day_and_reverts_to_long_run(garch_returns: pd.Series) -> None:
    fit = fit_garch(garch_returns)
    forecast = garch_forecast(fit, MAX_FORECAST_DAYS)
    assert list(forecast.index[[0, -1]]) == [1, MAX_FORECAST_DAYS]
    assert forecast.iloc[0] == pytest.approx(fit.conditional_volatility.iloc[-1])
    gaps = np.abs(forecast.to_numpy() - fit.long_run_volatility)
    assert np.all(np.diff(gaps) <= 1e-12)
    day = 10
    expected = fit.long_run_volatility**2 + fit.persistence ** (day - 1) * (
        forecast.iloc[0] ** 2 - fit.long_run_volatility**2
    )
    assert forecast.loc[day] == pytest.approx(np.sqrt(expected))


def test_horizon_volatility_averages_variance_not_volatility() -> None:
    forecast = pd.Series([0.1, 0.3])
    assert horizon_volatility(forecast) == pytest.approx(np.sqrt((0.01 + 0.09) / 2))


@pytest.mark.parametrize("horizon", [0, MAX_FORECAST_DAYS + 1, 2.5, True])
def test_forecast_rejects_bad_horizons(garch_returns: pd.Series, horizon: object) -> None:
    fit = fit_garch(garch_returns.iloc[:500])
    with pytest.raises(ValueError, match="horizon_days"):
        garch_forecast(fit, horizon)  # type: ignore[arg-type]


def test_garch_rejects_short_or_constant_history() -> None:
    with pytest.raises(ValueError, match=f"at least {MIN_GARCH_OBS}"):
        fit_garch(dated(np.random.default_rng(3).normal(0, 0.01, MIN_GARCH_OBS - 1)))
    with pytest.raises(ValueError, match="constant"):
        fit_garch(dated(np.full(MIN_GARCH_OBS, 0.001)))


def test_garch_reports_an_optimizer_failure(garch_returns: pd.Series) -> None:
    class Failed:
        success, x, message = False, np.array([0.1, 0.8]), "Iteration limit reached"

    with (
        pytest.MonkeyPatch.context() as patch,
        pytest.raises(ValueError, match="did not converge: Iteration limit reached"),
    ):
        patch.setattr("risklens.analytics.volatility.minimize", lambda *_, **__: Failed())
        fit_garch(garch_returns)
