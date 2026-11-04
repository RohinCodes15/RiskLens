"""Unit tests for turnover limits on minimum-volatility and maximum-Sharpe weights."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    max_sharpe_portfolio,
    min_volatility_portfolio,
    one_way_turnover,
    validate_turnover_limit,
)
from risklens.analytics.turnover_limit import turnover_constraints

CURRENT = [0.7, 0.1, 0.1, 0.1]


@pytest.fixture(scope="module")
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    daily = rng.normal([0.0008, 0.0003, 0.0005, 0.0002], [0.02, 0.008, 0.015, 0.01], (500, 4))
    return pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        index=pd.bdate_range("2023-01-02", periods=500),
        columns=["A", "B", "C", "D"],
    )


def test_one_way_turnover_counts_what_is_bought() -> None:
    assert one_way_turnover([0.5, 0.5], [0.7, 0.3]) == pytest.approx(0.2)
    assert one_way_turnover([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)
    assert one_way_turnover(CURRENT, CURRENT) == 0.0
    with pytest.raises(ValueError, match="Expected 4"):
        one_way_turnover(CURRENT, [0.5, 0.5])


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (-0.1, "between 0 and 1"),
        (1.5, "between 0 and 1"),
        (np.nan, "between 0 and 1"),
        (True, "a number"),
        ("0.2", "a number"),
    ],
)
def test_validate_turnover_limit_rejects_bad_values(value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_turnover_limit(value)  # type: ignore[arg-type]


def test_constraints_hold_exactly_at_the_current_weights() -> None:
    current = np.array(CURRENT)
    rows = turnover_constraints(current, 0.2)
    assert rows.shape == (9, 8)
    assert np.all(rows @ np.concatenate([current, np.zeros(4)]) >= -1e-12)  # 0 up to rounding
    moved = np.array([0.4, 0.2, 0.2, 0.2])  # turnover 0.3, over the 0.2 limit
    assert (rows @ np.concatenate([moved, np.abs(moved - current)]))[-1] < 0


@pytest.mark.parametrize("limit", [0.05, 0.1, 0.25])
@pytest.mark.parametrize("optimizer", [min_volatility_portfolio, max_sharpe_portfolio])
def test_limited_weights_stay_within_the_limit(
    prices: pd.DataFrame, optimizer: object, limit: float
) -> None:
    result = optimizer(prices, current_weights=CURRENT, max_turnover=limit)
    assert one_way_turnover(CURRENT, result.weights) <= limit + 1e-6
    assert result.weights.sum() == pytest.approx(1.0)
    assert (result.weights >= 0).all()


def test_tighter_limits_cost_volatility_and_sharpe(prices: pd.DataFrame) -> None:
    def volatility(limit: float) -> float:
        return min_volatility_portfolio(
            prices, current_weights=CURRENT, max_turnover=limit
        ).volatility

    def sharpe(limit: float) -> float:
        return max_sharpe_portfolio(
            prices, current_weights=CURRENT, max_turnover=limit
        ).sharpe_ratio

    assert volatility(0.05) > volatility(0.2) > volatility(0.4)
    assert sharpe(0.05) < sharpe(0.2) < sharpe(0.4)


def test_zero_limit_keeps_the_current_weights(prices: pd.DataFrame) -> None:
    for optimizer in (min_volatility_portfolio, max_sharpe_portfolio):
        result = optimizer(prices, current_weights=CURRENT, max_turnover=0.0)
        np.testing.assert_allclose(result.weights, CURRENT, atol=1e-6)


@pytest.mark.parametrize("optimizer", [min_volatility_portfolio, max_sharpe_portfolio])
def test_a_loose_limit_matches_the_unlimited_optimum(
    prices: pd.DataFrame, optimizer: object
) -> None:
    free = optimizer(prices)
    limited = optimizer(prices, current_weights=CURRENT, max_turnover=1.0)
    np.testing.assert_allclose(limited.weights, free.weights, atol=1e-5)


def test_limited_minimum_volatility_beats_random_feasible_weights(prices: pd.DataFrame) -> None:
    limit = 0.1
    best = min_volatility_portfolio(prices, current_weights=CURRENT, max_turnover=limit)
    cov = prices.pct_change().dropna().cov().to_numpy() * 252
    current = np.array(CURRENT)
    rng = np.random.default_rng(0)
    for target in rng.dirichlet(np.ones(4), 5000):
        step = min(1.0, limit / max(one_way_turnover(current, target), 1e-12))
        w = current + (target - current) * step  # shrunk onto the limit, so feasible
        assert np.sqrt(w @ cov @ w) >= best.volatility - 1e-9


def test_limit_needs_both_arguments(prices: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="both current_weights and max_turnover"):
        min_volatility_portfolio(prices, current_weights=CURRENT)
    with pytest.raises(ValueError, match="both current_weights and max_turnover"):
        max_sharpe_portfolio(prices, max_turnover=0.2)
    with pytest.raises(ValueError, match="Expected 4"):
        min_volatility_portfolio(prices, current_weights=[0.5, 0.5], max_turnover=0.2)
