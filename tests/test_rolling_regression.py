"""A single shock affects exactly the trailing windows that contain it."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics.rolling import rolling_max_drawdown, rolling_sharpe, rolling_volatility

WINDOW = 21
N_DAYS = 120
SHOCK_DAY = 50


def shocked(shock: float) -> pd.Series:
    """Steady 0.1% daily gains with one ``shock`` return on ``SHOCK_DAY``."""
    values = np.full(N_DAYS, 0.001)
    values[SHOCK_DAY] = shock
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=N_DAYS))


def windows_containing_shock() -> np.ndarray:
    positions = np.arange(N_DAYS)
    return (positions >= SHOCK_DAY) & (positions < SHOCK_DAY + WINDOW)


def test_volatility_is_raised_only_while_the_shock_is_in_the_window() -> None:
    vol = rolling_volatility(shocked(0.05), WINDOW).to_numpy()
    full = ~np.isnan(vol)

    assert (vol[windows_containing_shock()] > 0).all()
    assert (vol[full & ~windows_containing_shock()] == 0.0).all()


def test_max_drawdown_holds_the_drop_for_exactly_one_window() -> None:
    worst = rolling_max_drawdown(shocked(-0.05), WINDOW).to_numpy()
    full = ~np.isnan(worst)

    np.testing.assert_allclose(worst[windows_containing_shock()], -0.05)
    assert (worst[full & ~windows_containing_shock()] == 0.0).all()


def test_rolling_sharpe_ignores_leverage_at_a_zero_risk_free_rate() -> None:
    returns = pd.Series(
        np.random.default_rng(2).normal(0.0005, 0.01, N_DAYS),
        index=pd.bdate_range("2024-01-02", periods=N_DAYS),
    )

    base = rolling_sharpe(returns, WINDOW)

    pd.testing.assert_series_equal(rolling_sharpe(returns * 2.0, WINDOW), base)
    assert rolling_sharpe(returns * 2.0, WINDOW, 0.03).iloc[-1] != pytest.approx(
        rolling_sharpe(returns, WINDOW, 0.03).iloc[-1]
    )
