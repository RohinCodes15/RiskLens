"""Regression tests: stress tests on per-ticker price history (mocked yfinance)."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import HISTORICAL_SCENARIOS, custom_scenario, run_stress_tests, stress_test
from risklens.data import fetch_price_history, fetch_prices

COVID = HISTORICAL_SCENARIOS[1]  # 2020-02-19 to 2020-03-23


def yahoo(start: str, end: str, listings: dict[str, tuple[str | None, str | None]]) -> pd.DataFrame:
    """A ``yf.download`` style frame; each ticker trades only inside (listed, delisted)."""
    dates = pd.bdate_range(start, end)
    rng = np.random.default_rng(7)
    columns = {}
    for ticker, (listed, delisted) in listings.items():
        prices = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(dates)))), index=dates)
        if listed is not None:
            prices[prices.index < listed] = np.nan
        if delisted is not None:
            prices[prices.index > delisted] = np.nan
        columns[ticker] = prices
    return pd.concat({"Close": pd.DataFrame(columns)}, axis=1)


def history(raw: pd.DataFrame, tickers: list[str], start: str, end: str) -> pd.DataFrame:
    with patch("yfinance.download", return_value=raw):
        return fetch_price_history(tickers, start, end)


def test_recent_ipo_is_the_only_asset_blamed() -> None:
    raw = yahoo("2020-01-02", "2020-04-30", {"OLD": (None, None), "IPO": ("2020-03-02", None)})

    prices = history(raw, ["OLD", "IPO"], "2020-01-02", "2020-04-30")
    result = stress_test(prices, [0.5, 0.5], COVID)

    assert not result.available
    assert "IPO history starts 2020-03-02, after the scenario start 2020-02-19" in result.reason
    assert "OLD" not in result.reason


def test_common_dates_hid_which_asset_listed_late() -> None:
    # The bug this API fixes: fetch_prices trims OLD to IPO's dates, so both look short.
    raw = yahoo("2020-01-02", "2020-04-30", {"OLD": (None, None), "IPO": ("2020-03-02", None)})

    with patch("yfinance.download", return_value=raw):
        trimmed = fetch_prices(["OLD", "IPO"], "2020-01-02", "2020-04-30")

    assert "OLD history starts" in stress_test(trimmed, [0.5, 0.5], COVID).reason


def test_fully_covered_portfolio_matches_common_date_results() -> None:
    raw = yahoo("2020-01-02", "2020-04-30", {"A": (None, None), "B": (None, None)})

    full = stress_test(history(raw, ["A", "B"], "2020-01-02", "2020-04-30"), [0.6, 0.4], COVID)
    with patch("yfinance.download", return_value=raw):
        common = stress_test(
            fetch_prices(["A", "B"], "2020-01-02", "2020-04-30"), [0.6, 0.4], COVID
        )

    assert full.available and common.available
    assert full.first_date == pd.Timestamp("2020-02-19")
    assert full.last_date == pd.Timestamp("2020-03-23")
    assert full.n_returns == common.n_returns
    assert full.cumulative_return == pytest.approx(common.cumulative_return)
    assert full.max_drawdown == pytest.approx(common.max_drawdown)
    assert full.annualized_volatility == pytest.approx(common.annualized_volatility)


def test_missing_day_inside_window_is_dropped_not_reported() -> None:
    raw = yahoo("2020-01-02", "2020-04-30", {"A": (None, None), "B": (None, None)})
    raw.loc["2020-03-10", ("Close", "B")] = np.nan

    result = stress_test(history(raw, ["A", "B"], "2020-01-02", "2020-04-30"), [0.5, 0.5], COVID)

    assert result.available
    assert result.n_returns == len(pd.bdate_range(COVID.start, COVID.end)) - 2


def test_ticker_listed_after_the_window_has_no_price_data() -> None:
    raw = yahoo("2020-01-02", "2020-06-30", {"OLD": (None, None), "NEW": ("2020-05-01", None)})

    prices = history(raw, ["OLD", "NEW"], "2020-01-02", "2020-06-30")
    window_only = prices.loc[:"2020-03-31"]
    result = stress_test(window_only, [0.5, 0.5], COVID)

    assert "NEW has no price data" in result.reason
    assert "OLD" not in result.reason


def test_delisted_ticker_reports_the_scenario_end() -> None:
    raw = yahoo("2020-01-02", "2020-04-30", {"OLD": (None, None), "GONE": (None, "2020-03-02")})

    prices = history(raw, ["OLD", "GONE"], "2020-01-02", "2020-04-30")
    result = stress_test(prices, [0.5, 0.5], COVID)

    assert "GONE history ends 2020-03-02, before the scenario end 2020-03-23" in result.reason
    assert "OLD" not in result.reason


def test_every_scenario_names_only_the_late_listing() -> None:
    raw = yahoo("2007-01-02", "2022-12-30", {"SPY": (None, None), "IPO": ("2021-01-04", None)})

    prices = history(raw, ["SPY", "IPO"], "2007-01-02", "2022-12-30")
    results = run_stress_tests(prices, [0.7, 0.3])

    crisis, covid, bear = results
    for unavailable in (crisis, covid):
        assert not unavailable.available
        assert "IPO history starts 2021-01-04" in unavailable.reason
        assert "SPY" not in unavailable.reason
    assert bear.available and bear.n_returns > 0


def test_custom_window_after_listing_is_available() -> None:
    raw = yahoo("2020-01-02", "2020-06-30", {"OLD": (None, None), "IPO": ("2020-03-02", None)})

    prices = history(raw, ["OLD", "IPO"], "2020-01-02", "2020-06-30")
    result = stress_test(prices, [0.5, 0.5], custom_scenario("2020-03-02", "2020-06-30"))

    assert result.available
    assert result.first_date == pd.Timestamp("2020-03-02")
