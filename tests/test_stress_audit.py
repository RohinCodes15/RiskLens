"""Audit tests for historical stress windows: edges, alignment, and calculations."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    HISTORICAL_SCENARIOS,
    StressScenario,
    analyze_portfolio,  # noqa: F401 - used by the TODO(human) cross-check below
    custom_scenario,
    stress_test,
)


def prices(start: str, end: str, seed: int = 0, assets: str = "AB") -> pd.DataFrame:
    dates = pd.bdate_range(start, end)
    steps = np.random.default_rng(seed).normal(0.0, 0.01, (len(dates), len(assets)))
    return pd.DataFrame(100 * np.exp(np.cumsum(steps, axis=0)), index=dates, columns=list(assets))


def test_documented_scenarios_have_expected_peak_to_trough_dates() -> None:
    windows = {s.name: (s.start, s.end) for s in HISTORICAL_SCENARIOS}

    assert windows == {
        "2008 financial crisis": (pd.Timestamp("2007-10-09"), pd.Timestamp("2009-03-09")),
        "2020 COVID crash": (pd.Timestamp("2020-02-19"), pd.Timestamp("2020-03-23")),
        "2022 bear market": (pd.Timestamp("2022-01-03"), pd.Timestamp("2022-10-12")),
    }
    assert all(s.description for s in HISTORICAL_SCENARIOS)


def test_realized_return_is_the_daily_rebalanced_product() -> None:
    data = prices("2024-01-02", "2024-03-29")
    scenario = custom_scenario("2024-02-01", "2024-02-29")
    result = stress_test(data, [0.3, 0.7], scenario)

    window = data.loc["2024-02-01":"2024-02-29"]
    daily = window.pct_change().dropna() @ np.array([0.3, 0.7])
    assert result.cumulative_return == pytest.approx(np.prod(1 + daily) - 1)
    assert result.n_returns == len(window) - 1
    assert (result.first_date, result.last_date) == (window.index[0], window.index[-1])


def test_prices_outside_the_window_do_not_change_results() -> None:
    data = prices("2024-01-02", "2024-03-29")
    scenario = custom_scenario("2024-02-01", "2024-02-29")
    shocked = data.copy()
    shocked.loc[:"2024-01-31"] *= 3.0
    shocked.loc["2024-03-01":] *= 0.1

    assert stress_test(data, [0.5, 0.5], scenario) == stress_test(shocked, [0.5, 0.5], scenario)


def test_different_asset_calendars_use_only_common_actual_prices() -> None:
    data = prices("2024-01-02", "2024-02-29")
    data.loc["2024-01-17", "A"] = np.nan
    data.loc["2024-01-24", "B"] = np.nan
    result = stress_test(data, [0.5, 0.5], custom_scenario("2024-01-02", "2024-02-29"))

    assert result.available
    assert result.n_returns == len(data.dropna()) - 1


@pytest.mark.parametrize(("first_price", "available"), [("2024-01-08", True), ("2024-01-09", True),
                                                        ("2024-01-10", False), ("2024-01-11", False)])
def test_late_listing_allows_at_most_one_missing_weekday(first_price: str, available: bool) -> None:
    data = prices(first_price, "2024-02-29")
    result = stress_test(data, [0.5, 0.5], custom_scenario("2024-01-08", "2024-02-29"))

    assert result.available is available


@pytest.mark.parametrize(("last_price", "available"), [("2024-02-29", True), ("2024-02-28", True),
                                                       ("2024-02-27", False)])
def test_early_history_end_allows_at_most_one_missing_weekday(last_price: str, available: bool) -> None:
    data = prices("2024-01-02", last_price)
    result = stress_test(data, [0.5, 0.5], custom_scenario("2024-01-08", "2024-02-29"))

    assert result.available is available


def test_holiday_monday_end_with_friday_last_price_is_available() -> None:
    data = prices("2024-01-02", "2024-02-16")  # Feb 19 2024 was Presidents' Day
    result = stress_test(data, [0.5, 0.5], custom_scenario("2024-01-08", "2024-02-19"))

    assert result.available and result.last_date == pd.Timestamp("2024-02-16")


def test_unavailable_scenario_reports_no_metrics() -> None:
    data = prices("2015-01-02", "2015-12-31")
    result = stress_test(data, [0.5, 0.5], HISTORICAL_SCENARIOS[0])

    assert not result.available
    assert result.reason.startswith("Insufficient history")
    fields = (result.cumulative_return, result.max_drawdown, result.annualized_volatility)
    assert fields == (None, None, None) and result.n_returns == 0


def test_timezone_aware_prices_are_aligned_by_calendar_date() -> None:
    data = prices("2024-01-02", "2024-02-29")
    aware = data.tz_localize("America/New_York")
    scenario = custom_scenario("2024-01-10", "2024-02-20")

    naive, tz = stress_test(data, [0.5, 0.5], scenario), stress_test(aware, [0.5, 0.5], scenario)
    assert tz.cumulative_return == pytest.approx(naive.cumulative_return)
    assert tz.n_returns == naive.n_returns


def test_scenario_dates_are_normalized_at_construction() -> None:
    scenario = StressScenario(" Crash ", pd.Timestamp("2024-01-08 15:30", tz="UTC"), "2024-02-01")

    assert scenario.name == "Crash"
    assert scenario.start == pd.Timestamp("2024-01-08") and scenario.start.tz is None
    assert scenario.end == pd.Timestamp("2024-02-01")


@pytest.mark.parametrize(
    ("args", "message"),
    [(("x", "2024-02-01", "2024-01-15"), "before end"), (("", "2024-01-01", "2024-02-01"), "blank"),
     (("x", "soon", "2024-02-01"), "not a valid date")],
)
def test_invalid_scenarios_are_rejected_at_construction(args: tuple, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        StressScenario(*args)


@pytest.mark.parametrize("scenario", ["2020 COVID crash", None, ("2020-01-01", "2020-02-01")])
def test_non_scenario_argument_raises_value_error(scenario: object) -> None:
    with pytest.raises(ValueError, match="StressScenario"):
        stress_test(prices("2024-01-02", "2024-02-29"), [0.5, 0.5], scenario)


def test_stress_window_matches_analyze_portfolio_on_the_same_prices() -> None:
    """Cross-check: a stress window equals analyze_portfolio on that window."""
    # TODO(human): Replace the next line with the 11-line cross-check (four spaces).
    pytest.skip("TODO(human): write the stress vs. analyze_portfolio cross-check.")
