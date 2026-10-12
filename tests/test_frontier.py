"""Deterministic tests for the long-only efficient frontier."""

import numpy as np
import pandas as pd
import pytest
from test_optimization import five_assets, random_portfolios

from risklens.analytics import (
    EfficientFrontier,
    OptimizationError,
    analyze_portfolio,
    efficient_frontier,
    estimate_inputs,
    frontier_point_within_risk,
    min_volatility_portfolio,
    optimization,
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


# --- validation and edge cases -------------------------------------------------------


@pytest.mark.parametrize("n_points", [1, 101, 2.5, True, "40"])
def test_invalid_point_counts_are_rejected(n_points: object) -> None:
    with pytest.raises(ValueError, match="n_points must be"):
        efficient_frontier(five_assets(), n_points=n_points)  # type: ignore[arg-type]


def test_invalid_risk_free_rate_is_rejected() -> None:
    with pytest.raises(ValueError, match="annual fraction"):
        efficient_frontier(five_assets(), risk_free_rate=4.0)


def test_equal_expected_returns_give_the_single_min_volatility_point() -> None:
    swings = np.tile([0.01, -0.01], 100)
    returns = np.column_stack([swings, 2 * swings]) + 5e-4  # same mean, different risk
    growth = np.vstack([np.ones((1, 2)), np.cumprod(1 + returns, axis=0)])  # keep every return
    prices = pd.DataFrame(
        100 * growth,
        index=pd.bdate_range("2022-01-03", periods=len(growth)),
        columns=["calm", "wild"],
    )
    expected, _, _ = estimate_inputs(prices)
    assert expected["calm"] == pytest.approx(expected["wild"])

    frontier = efficient_frontier(prices)

    assert len(frontier.points) == 1
    assert frontier.weights.iloc[0]["calm"] == pytest.approx(1.0, abs=1e-6)


# --- solver failure -------------------------------------------------------------------


def test_infeasible_targets_are_dropped_and_counted(monkeypatch: pytest.MonkeyPatch) -> None:
    solve = optimization._target_return_solve
    calls = iter(range(100))

    def every_third_fails(*args: object) -> object:
        if next(calls) % 3 == 1:
            raise OptimizationError("target unreachable")
        return solve(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(optimization, "_target_return_solve", every_third_fails)

    frontier = efficient_frontier(five_assets(), n_points=30)

    assert frontier.infeasible_targets == 10
    assert len(frontier.points) == len(frontier.weights) == 20
    assert frontier.points["expected_return"].is_monotonic_increasing


def test_frontier_with_no_solvable_point_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def always_fails(*args: object) -> object:
        raise OptimizationError("target unreachable")

    monkeypatch.setattr(optimization, "_target_return_solve", always_fails)

    with pytest.raises(OptimizationError, match="No efficient frontier point"):
        efficient_frontier(five_assets())


# --- point within a volatility budget ---------------------------------------------------


def test_within_risk_picks_highest_return_point_not_riskier_than_budget() -> None:
    frontier = efficient_frontier(five_assets(), n_points=12)
    budget = float(frontier.points["volatility"].median())
    index = frontier_point_within_risk(frontier, budget)
    allowed = frontier.points[frontier.points["volatility"] <= budget + 1e-6]
    assert index == allowed["expected_return"].idxmax()
    assert frontier.points.loc[index, "volatility"] <= budget + 1e-6


def test_within_risk_matches_a_point_exactly_on_the_budget() -> None:
    frontier = efficient_frontier(five_assets(), n_points=12)
    assert frontier_point_within_risk(frontier, frontier.points["volatility"].iloc[5]) == 5


def test_within_risk_returns_last_point_for_a_large_budget() -> None:
    frontier = efficient_frontier(five_assets(), n_points=12)
    assert frontier_point_within_risk(frontier, 10.0) == frontier.points.index[-1]


def test_within_risk_returns_none_when_every_point_is_riskier() -> None:
    frontier = efficient_frontier(five_assets(), n_points=12)
    assert frontier_point_within_risk(frontier, 0.0) is None


@pytest.mark.parametrize("volatility", [-0.01, float("nan"), float("inf"), True, "0.2", None])
def test_within_risk_rejects_invalid_volatility(volatility: object) -> None:
    frontier = efficient_frontier(five_assets(), n_points=3)
    with pytest.raises(ValueError, match="current_volatility"):
        frontier_point_within_risk(frontier, volatility)  # type: ignore[arg-type]


def test_within_risk_accepts_numpy_and_int_budgets() -> None:
    frontier = efficient_frontier(five_assets(), n_points=3)
    assert frontier_point_within_risk(frontier, np.float64(10.0)) == 2
    assert frontier_point_within_risk(frontier, 0) is None
