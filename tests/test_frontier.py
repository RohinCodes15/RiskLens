"""Deterministic tests for the long-only efficient frontier."""

import numpy as np
import pytest
from test_optimization import five_assets, random_portfolios

from risklens.analytics import (
    EfficientFrontier,
    analyze_portfolio,
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


# --- each point is a valid, optimal portfolio ------------------------------------------


def test_frontier_weights_are_long_only_and_metrics_match_engine() -> None:
    prices = five_assets()
    frontier = efficient_frontier(prices, n_points=10, risk_free_rate=0.02)

    assert (frontier.weights.to_numpy() >= 0).all()
    np.testing.assert_allclose(frontier.weights.sum(axis=1), 1.0, atol=1e-12)
    for i, weights in frontier.weights.iterrows():
        engine = analyze_portfolio(prices, weights.to_list(), risk_free_rate=0.02)
        point = frontier.points.loc[i]
        assert point["expected_return"] == pytest.approx(engine.annualized_return, rel=1e-9)
        assert point["volatility"] == pytest.approx(engine.annualized_volatility, rel=1e-9)
        assert point["sharpe_ratio"] == pytest.approx(engine.sharpe_ratio, rel=1e-9)


def test_no_sampled_portfolio_beats_a_frontier_point() -> None:
    prices = five_assets()
    frontier = efficient_frontier(prices, n_points=20)
    expected, covariance, _ = estimate_inputs(prices)
    samples = random_portfolios(len(expected))
    sample_returns = samples @ expected.to_numpy()
    sample_vols = np.sqrt(np.einsum("ij,jk,ik->i", samples, covariance.to_numpy(), samples))

    for _, point in frontier.points.iterrows():
        reaches = sample_returns >= point["expected_return"]
        assert sample_vols[reaches].min() >= point["volatility"] - 1e-8
