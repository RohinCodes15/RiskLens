"""Unit tests for historical stress testing on synthetic adjusted prices."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    HISTORICAL_SCENARIOS,
    TRADING_DAYS_PER_YEAR,
    StressResult,
    custom_scenario,
    run_stress_tests,
    stress_test,
)


def prices() -> pd.DataFrame:
    # Window Jan 3-8: A returns +10%, -10%, 0%; B returns 0%, +10%, -20%.
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"])
    return pd.DataFrame(
        {"A": [90.0, 100.0, 110.0, 99.0, 99.0], "B": [40.0, 50.0, 50.0, 55.0, 44.0]},
        index=dates,
    )


WINDOW = custom_scenario("2024-01-03", "2024-01-08")


def test_metrics_cover_only_the_window_and_match_hand_calculation() -> None:
    result = stress_test(prices(), [0.5, 0.5], WINDOW)
    daily = np.array([0.05, 0.0, -0.10])

    assert isinstance(result, StressResult)
    assert result.available and result.reason is None
    assert result.first_date == pd.Timestamp("2024-01-03")  # Jan 2 price excluded
    assert result.last_date == pd.Timestamp("2024-01-08")
    assert result.n_returns == 3
    assert result.cumulative_return == pytest.approx(np.prod(1 + daily) - 1)
    assert result.max_drawdown == pytest.approx(-0.10)
    vol = np.std(daily, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert result.annualized_volatility == pytest.approx(vol)
    assert "not the portfolio's actual historical holdings" in result.note


def test_missing_day_is_dropped_not_filled() -> None:
    gappy = prices()
    gappy.loc["2024-01-04", "B"] = np.nan
    before = gappy.copy()

    result = stress_test(gappy, [0.5, 0.5], WINDOW)

    # Jan 3 -> Jan 5 becomes one real two-day return: A -1%, B +10%.
    expected = (1 + 0.5 * (99 / 100 - 1) + 0.5 * (55 / 50 - 1)) * (1 + 0.5 * -0.2) - 1
    assert result.n_returns == 2
    assert result.cumulative_return == pytest.approx(expected)
    pd.testing.assert_frame_equal(gappy, before)  # input not mutated


def test_asset_listed_after_window_start_is_unavailable() -> None:
    late = prices()
    late.loc[:"2024-01-04", "B"] = np.nan
    scenario = custom_scenario("2023-12-20", "2024-01-08")

    result = stress_test(late, [0.5, 0.5], scenario)

    assert not result.available
    assert "B history starts 2024-01-05" in result.reason
    assert result.cumulative_return is None and result.max_drawdown is None
    assert result.annualized_volatility is None


def test_history_ending_before_window_end_is_unavailable() -> None:
    result = stress_test(prices(), [0.5, 0.5], custom_scenario("2024-01-03", "2024-02-01"))

    assert not result.available
    assert "history ends 2024-01-08" in result.reason


def test_weekend_window_edges_are_tolerated() -> None:
    # Saturday Dec 30 start and Sunday Jan 7 end around actual trading days.
    result = stress_test(prices(), [1.0, 0.0], custom_scenario("2023-12-30", "2024-01-07"))

    assert result.available
    assert result.first_date == pd.Timestamp("2024-01-02")
    assert result.last_date == pd.Timestamp("2024-01-05")


def test_too_few_common_prices_is_unavailable() -> None:
    result = stress_test(prices(), [0.5, 0.5], custom_scenario("2024-01-03", "2024-01-04"))

    assert not result.available
    assert "Need 3 common price dates" in result.reason


def test_run_stress_tests_keeps_documented_scenarios_in_order() -> None:
    names = [s.name for s in HISTORICAL_SCENARIOS]
    assert names == ["2008 financial crisis", "2020 COVID crash", "2022 bear market"]

    dates = pd.bdate_range("2019-01-01", "2023-01-31")
    synthetic = pd.DataFrame({"A": np.linspace(100, 200, len(dates))}, index=dates)
    results = run_stress_tests(synthetic, [1.0])

    assert [r.scenario.name for r in results] == names
    assert not results[0].available  # synthetic history starts 2019
    assert results[1].available and results[2].available
    assert results[1].cumulative_return > 0  # steadily rising prices


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2024-01-08", "2024-01-03", "before end"),
        ("2024-01-03", "2024-01-03", "before end"),
        ("not a date", "2024-01-03", "not a valid date"),
        (None, "2024-01-03", "missing"),
    ],
)
def test_custom_scenario_rejects_bad_dates(start: object, end: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        custom_scenario(start, end)


def test_custom_scenario_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="blank"):
        custom_scenario("2024-01-03", "2024-01-08", name="  ")


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (pd.DataFrame({"A": [1.0, 2.0, 3.0]}), "indexed by date"),
        (prices().iloc[::-1], "sorted and unique"),
        (prices().assign(A=-1.0), "positive"),
        (prices().assign(A="x"), "numbers"),
        ("prices", "DataFrame"),
    ],
)
def test_invalid_prices_raise(bad: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        stress_test(bad, [0.5, 0.5], WINDOW)


def test_invalid_weights_raise() -> None:
    with pytest.raises(ValueError):
        stress_test(prices(), [0.7, 0.7], WINDOW)
