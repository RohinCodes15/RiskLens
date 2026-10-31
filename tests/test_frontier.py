"""Deterministic tests for the long-only efficient frontier."""

import pytest
from test_optimization import five_assets

from risklens.analytics import (
    EfficientFrontier,
    efficient_frontier,
    estimate_inputs,
    min_volatility_portfolio,
)

# --- shape and endpoints ------------------------------------------------------------


def test_frontier_has_requested_points_in_increasing_return_order() -> None:
    frontier = efficient_frontier(five_assets(), n_points=30)

    assert isinstance(frontier, EfficientFrontier)
    assert len(frontier.points) == 30
    assert frontier.infeasible_targets == 0
    assert list(frontier.points.columns) == ["expected_return", "volatility", "sharpe_ratio"]
    assert list(frontier.weights.columns) == list(five_assets().columns)
    assert frontier.weights.index.equals(frontier.points.index)
    assert frontier.points["expected_return"].is_monotonic_increasing
    assert frontier.points["volatility"].diff().dropna().min() >= -1e-9


def test_frontier_runs_from_min_volatility_to_best_single_asset() -> None:
    prices = five_assets()
    frontier = efficient_frontier(prices)
    lowest = min_volatility_portfolio(prices)
    expected, _, _ = estimate_inputs(prices)

    first, last = frontier.points.iloc[0], frontier.points.iloc[-1]
    assert first["expected_return"] == pytest.approx(lowest.expected_return, abs=1e-6)
    assert first["volatility"] == pytest.approx(lowest.volatility, rel=1e-5)
    assert last["expected_return"] == pytest.approx(expected.max(), abs=1e-6)
    assert frontier.weights.iloc[-1][expected.idxmax()] == pytest.approx(1.0, abs=1e-5)
