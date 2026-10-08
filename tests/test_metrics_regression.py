"""Invariants of the risk metrics: order, confidence, exposure, and diversification."""

from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    historical_cvar,
    historical_var,
)

N_DAYS = 500
TailMeasure = Callable[..., float]


def dated(values: list[float] | np.ndarray) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2023-01-02", periods=len(values)))


def noisy(seed: int = 4) -> pd.Series:
    return dated(np.random.default_rng(seed).normal(0.0004, 0.012, N_DAYS))


def three_assets() -> pd.DataFrame:
    rng = np.random.default_rng(8)
    corr = np.array([[1.0, 0.3, 0.1], [0.3, 1.0, 0.4], [0.1, 0.4, 1.0]])
    shocks = rng.standard_normal((N_DAYS, 3)) @ np.linalg.cholesky(corr).T
    values = np.array([3e-4, 5e-4, 2e-4]) + shocks * np.array([0.010, 0.020, 0.015])
    return pd.DataFrame(values, index=noisy().index, columns=["A", "B", "C"])


@pytest.mark.parametrize("measure", [historical_var, historical_cvar])
def test_tail_risk_ignores_the_order_of_returns(measure: TailMeasure) -> None:
    returns = noisy()
    shuffled = dated(np.random.default_rng(0).permutation(returns.to_numpy()))

    # Exact up to float summation order in the tail mean.
    assert measure(shuffled) == pytest.approx(measure(returns), rel=1e-12)


@pytest.mark.parametrize("measure", [historical_var, historical_cvar])
def test_tail_risk_rises_with_confidence(measure: TailMeasure) -> None:
    returns = noisy()

    levels = [measure(returns, c) for c in (0.90, 0.95, 0.975, 0.99)]

    assert levels == sorted(levels)
    assert levels[0] < levels[-1]


@pytest.mark.parametrize("measure", [historical_var, historical_cvar])
def test_tail_risk_scales_with_exposure(measure: TailMeasure) -> None:
    returns = noisy()

    assert measure(returns * 2.0) == pytest.approx(2.0 * measure(returns))
