"""Turnover on rebalance dates and trading costs charged in portfolio_returns."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    REBALANCE_FREQUENCIES,
    rebalance_turnover,
)

WEIGHTS = [0.5, 0.3, 0.2]
PERIOD_CODES = {"monthly": "M", "quarterly": "Q", "annual": "Y"}


@pytest.fixture
def returns() -> pd.DataFrame:
    """Daily returns for three assets over about a year and a quarter."""
    rng = np.random.default_rng(1)
    index = pd.bdate_range("2024-01-01", periods=320)
    return pd.DataFrame(rng.normal(0.0005, 0.02, (320, 3)), index=index, columns=["A", "B", "C"])


def resets(returns: pd.DataFrame, rebalance: str) -> np.ndarray:
    """True on each return date where holdings go back to target weights."""
    if rebalance == "daily":
        flags = np.ones(len(returns), dtype=bool)
    elif rebalance == "never":
        flags = np.zeros(len(returns), dtype=bool)
    else:
        periods = returns.index.to_period(PERIOD_CODES[rebalance])
        flags = np.r_[False, periods[1:] != periods[:-1]]
    flags[0] = False
    return flags


def walk(returns: pd.DataFrame, rebalance: str, cost_bps: float) -> tuple[np.ndarray, np.ndarray]:
    """Reference dollar walk: ``(net daily returns, one-way turnover)``."""
    target = np.array(WEIGHTS)
    holdings = target.copy()
    net, turnover = [], []
    for reset, row in zip(resets(returns, rebalance), returns.to_numpy(), strict=True):
        start = holdings.sum()
        traded = np.abs(target * start - holdings).sum() if reset else 0.0
        if reset:
            holdings = target * (start - cost_bps / 10_000 * traded)
        turnover.append(traded / 2 / start)
        holdings = holdings * (1 + row)
        net.append(holdings.sum() / start - 1)
    return np.array(net), np.array(turnover)


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_turnover_matches_a_dollar_walk(returns: pd.DataFrame, rebalance: str) -> None:
    result = rebalance_turnover(returns, WEIGHTS, rebalance)
    np.testing.assert_allclose(result.to_numpy(), walk(returns, rebalance, 0.0)[1], atol=1e-15)
    assert result.name == "turnover"
    pd.testing.assert_index_equal(result.index, returns.index)


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_turnover_is_zero_off_rebalance_dates_and_on_the_first(
    returns: pd.DataFrame, rebalance: str
) -> None:
    result = rebalance_turnover(returns, WEIGHTS, rebalance).to_numpy()
    assert result[0] == 0.0
    assert np.all(result[~resets(returns, rebalance)] == 0.0)
    assert np.all(result[resets(returns, rebalance)] > 0.0)


def test_turnover_for_a_known_drift() -> None:
    """A doubles from 50/50 to 2/3 vs 1/3: selling 1/6 of the portfolio resets it."""
    index = pd.bdate_range("2024-01-01", periods=2)
    returns = pd.DataFrame({"A": [1.0, 0.0], "B": [0.0, 0.0]}, index=index)
    result = rebalance_turnover(returns, [0.5, 0.5], "daily")
    np.testing.assert_allclose(result.to_numpy(), [0.0, 1 / 6])


def test_turnover_falls_as_rebalancing_gets_rarer(returns: pd.DataFrame) -> None:
    totals = [rebalance_turnover(returns, WEIGHTS, f).sum() for f in REBALANCE_FREQUENCIES]
    assert totals == sorted(totals, reverse=True)
    assert totals[-1] == 0.0


def test_identical_assets_never_need_trading(returns: pd.DataFrame) -> None:
    same = pd.DataFrame({name: returns["A"] for name in ["X", "Y", "Z"]})
    np.testing.assert_allclose(rebalance_turnover(same, WEIGHTS, "daily"), 0.0, atol=1e-15)


def test_turnover_rejects_the_same_input_as_portfolio_returns(returns: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="rebalance must be one of"):
        rebalance_turnover(returns, WEIGHTS, "weekly")
    with pytest.raises(ValueError, match="Expected 3 weight"):
        rebalance_turnover(returns, [1.0], "daily")
