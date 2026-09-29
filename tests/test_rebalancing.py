"""Rebalance frequencies in portfolio_returns: drift, resets, and input rejection."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import REBALANCE_FREQUENCIES, cumulative_wealth, portfolio_returns
from risklens.data import to_returns

WEIGHTS = [0.5, 0.3, 0.2]
PERIOD_CODES = {"monthly": "M", "quarterly": "Q", "annual": "Y"}


@pytest.fixture
def prices() -> pd.DataFrame:
    """Two years of random-walk adjusted prices for three assets."""
    rng = np.random.default_rng(0)
    growth = np.cumprod(1 + rng.normal(0.0004, 0.015, (520, 3)), axis=0)
    index = pd.bdate_range("2022-01-03", periods=520)
    return pd.DataFrame(100 * growth, index=index, columns=["A", "B", "C"])


@pytest.fixture
def returns(prices: pd.DataFrame) -> pd.DataFrame:
    return to_returns(prices)


def walk(returns: pd.DataFrame, weights: list[float], rebalance: str) -> np.ndarray:
    """Reference: hold dollar positions day by day, resetting on each new period."""
    holdings = np.array(weights, dtype=float)
    out = []
    for i, (day, row) in enumerate(returns.iterrows()):
        if i > 0:
            previous = returns.index[i - 1]
            if rebalance == "daily" or (
                rebalance in PERIOD_CODES
                and day.to_period(PERIOD_CODES[rebalance])
                != previous.to_period(PERIOD_CODES[rebalance])
            ):
                holdings = np.array(weights) * holdings.sum()
        start = holdings.sum()
        holdings = holdings * (1 + row.to_numpy())
        out.append(holdings.sum() / start - 1)
    return np.array(out)


def test_daily_is_the_weighted_sum_of_asset_returns(returns: pd.DataFrame) -> None:
    result = portfolio_returns(returns, WEIGHTS, "daily")
    np.testing.assert_array_equal(result.to_numpy(), returns.to_numpy() @ np.array(WEIGHTS))


def test_default_frequency_is_daily(returns: pd.DataFrame) -> None:
    pd.testing.assert_series_equal(
        portfolio_returns(returns, WEIGHTS), portfolio_returns(returns, WEIGHTS, "daily")
    )


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_every_frequency_matches_a_day_by_day_holdings_walk(
    returns: pd.DataFrame, rebalance: str
) -> None:
    result = portfolio_returns(returns, WEIGHTS, rebalance)
    np.testing.assert_allclose(result.to_numpy(), walk(returns, WEIGHTS, rebalance))


def test_never_equals_separately_invested_sleeves(
    prices: pd.DataFrame, returns: pd.DataFrame
) -> None:
    """Buy-and-hold is each starting dollar amount left to grow on its own."""
    sleeves = (prices / prices.iloc[0] * WEIGHTS).sum(axis=1)
    wealth = cumulative_wealth(portfolio_returns(returns, WEIGHTS, "never"))
    np.testing.assert_allclose(wealth.to_numpy(), sleeves.iloc[1:].to_numpy())


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_identical_assets_give_the_same_result_at_every_frequency(
    returns: pd.DataFrame, rebalance: str
) -> None:
    same = pd.DataFrame({name: returns["A"] for name in ["X", "Y", "Z"]})
    np.testing.assert_allclose(
        portfolio_returns(same, WEIGHTS, rebalance).to_numpy(), returns["A"].to_numpy()
    )


@pytest.mark.parametrize("rebalance", REBALANCE_FREQUENCIES)
def test_one_asset_ignores_the_frequency(returns: pd.DataFrame, rebalance: str) -> None:
    single = returns[["A"]]
    np.testing.assert_allclose(
        portfolio_returns(single, [1.0], rebalance).to_numpy(), returns["A"].to_numpy()
    )


def test_monthly_resets_on_the_first_return_date_of_each_month() -> None:
    """Day 1 drifts, so day 2 differs from target weights; Feb 1 resets them."""
    index = pd.DatetimeIndex(["2024-01-30", "2024-01-31", "2024-02-01"])
    returns = pd.DataFrame({"A": [1.0, 0.0, 0.10], "B": [0.0, 0.0, 0.0]}, index=index)
    result = portfolio_returns(returns, [0.5, 0.5], "monthly")
    # After A doubles, A is 2/3 of the portfolio; on Feb 1 it is back to 1/2.
    np.testing.assert_allclose(result.to_numpy(), [0.5, 0.0, 0.05])
    never = portfolio_returns(returns, [0.5, 0.5], "never")
    np.testing.assert_allclose(never.to_numpy(), [0.5, 0.0, 0.10 * 2 / 3])


def test_time_zone_dates_use_their_local_calendar(returns: pd.DataFrame) -> None:
    aware = returns.tz_localize("America/New_York")
    np.testing.assert_allclose(
        portfolio_returns(aware, WEIGHTS, "quarterly").to_numpy(),
        portfolio_returns(returns, WEIGHTS, "quarterly").to_numpy(),
    )


def test_portfolio_wipeout_stays_finite(returns: pd.DataFrame) -> None:
    crashed = returns.copy()
    crashed.iloc[5] = -1.0
    result = portfolio_returns(crashed, WEIGHTS, "annual")
    assert np.isfinite(result).all()
    assert cumulative_wealth(result).iloc[5:].eq(0).all()


def test_frequency_does_not_mutate_inputs(returns: pd.DataFrame) -> None:
    before = returns.copy()
    weights = list(WEIGHTS)
    portfolio_returns(returns, weights, "monthly")
    pd.testing.assert_frame_equal(returns, before)
    assert weights == WEIGHTS


@pytest.mark.parametrize("rebalance", ["weekly", "Monthly", "", None])
def test_unknown_frequency_is_rejected(returns: pd.DataFrame, rebalance: object) -> None:
    with pytest.raises(ValueError, match="rebalance must be one of"):
        portfolio_returns(returns, WEIGHTS, rebalance)  # type: ignore[arg-type]


@pytest.mark.parametrize("rebalance", ["monthly", "quarterly", "annual"])
def test_calendar_frequencies_need_dates(returns: pd.DataFrame, rebalance: str) -> None:
    with pytest.raises(ValueError, match="indexed by date"):
        portfolio_returns(returns.reset_index(drop=True), WEIGHTS, rebalance)


@pytest.mark.parametrize("rebalance", ["daily", "never"])
def test_daily_and_never_accept_undated_returns(returns: pd.DataFrame, rebalance: str) -> None:
    undated = returns.reset_index(drop=True)
    assert len(portfolio_returns(undated, WEIGHTS, rebalance)) == len(undated)


def test_calendar_frequencies_need_sorted_dates(returns: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="sorted and unique"):
        portfolio_returns(returns.iloc[::-1], WEIGHTS, "monthly")
