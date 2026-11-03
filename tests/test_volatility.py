"""Unit tests for EWMA and GARCH(1,1) volatility forecasts."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    EWMA_LAMBDA,
    ewma_volatility,
)

ANNUALIZE = np.sqrt(252)


def dated(values: np.ndarray) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2015-01-02", periods=len(values)))


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
