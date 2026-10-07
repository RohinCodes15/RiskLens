"""Optimality certificates and invariances for the long-only optimizers."""

import numpy as np
import pandas as pd
import pytest
from test_optimization import five_assets, make_prices

from risklens.analytics import (
    efficient_frontier,
    estimate_inputs,
    max_sharpe_portfolio,
    min_volatility_portfolio,
)

ACTIVE_WEIGHT = 1e-6
KKT_TOLERANCE = 1e-6


def redundant_assets() -> pd.DataFrame:
    """A2 is riskier than A0 and 95% correlated with it, so long-only min-vol drops it."""
    corr = np.array([[1.0, 0.0, 0.95], [0.0, 1.0, 0.0], [0.95, 0.0, 1.0]])
    return make_prices([3e-4, 4e-4, 5e-4], [0.010, 0.012, 0.030], corr=corr)


def assert_kkt(weights: np.ndarray, covariance: np.ndarray, direction: np.ndarray) -> None:
    """Check KKT for min w'Cw s.t. direction @ w = const, w >= 0.

    At the optimum, (C w)_i = c * direction_i on assets held, and
    (C w)_i >= c * direction_i on assets left out (raising them would add risk).
    """
    marginal = covariance @ weights
    held = weights > ACTIVE_WEIGHT
    c = float(np.mean(marginal[held] / direction[held]))
    residual = (marginal - c * direction) / np.abs(marginal).max()
    np.testing.assert_allclose(residual[held], 0.0, atol=KKT_TOLERANCE)
    assert (residual[~held] >= -KKT_TOLERANCE).all()


def test_min_volatility_satisfies_kkt_with_a_binding_long_only_bound() -> None:
    prices = redundant_assets()
    _, covariance, _ = estimate_inputs(prices)

    weights = min_volatility_portfolio(prices).weights.to_numpy()

    assert weights[2] == pytest.approx(0.0, abs=ACTIVE_WEIGHT)
    assert (weights[:2] > 0.1).all()
    assert_kkt(weights, covariance.to_numpy(), np.ones(3))


@pytest.mark.parametrize("risk_free_rate", [0.0, 0.05])
def test_max_sharpe_satisfies_kkt_conditions(risk_free_rate: float) -> None:
    prices = five_assets()
    expected, covariance, _ = estimate_inputs(prices)

    weights = max_sharpe_portfolio(prices, risk_free_rate).weights.to_numpy()

    assert_kkt(weights, covariance.to_numpy(), expected.to_numpy() - risk_free_rate)


def test_max_sharpe_is_at_least_every_frontier_point() -> None:
    prices = five_assets()
    best = max_sharpe_portfolio(prices, risk_free_rate=0.02)
    frontier = efficient_frontier(prices, n_points=100, risk_free_rate=0.02)

    frontier_best = frontier.points["sharpe_ratio"].max()
    assert best.sharpe_ratio >= frontier_best - 1e-9
    assert best.sharpe_ratio == pytest.approx(frontier_best, rel=1e-3)


def test_first_frontier_point_holds_the_min_volatility_weights() -> None:
    prices = five_assets()

    frontier = efficient_frontier(prices)

    lowest = min_volatility_portfolio(prices).weights
    np.testing.assert_allclose(frontier.weights.iloc[0], lowest, atol=1e-5)
