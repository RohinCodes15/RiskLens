"""Regression tests for stress-window boundaries and hand-checkable results."""

import numpy as np
import pandas as pd
import pytest
from test_stress import WINDOW, prices

from risklens.analytics import TRADING_DAYS_PER_YEAR, custom_scenario, stress_test


def test_exactly_three_common_prices_is_available() -> None:
    result = stress_test(prices(), [0.5, 0.5], custom_scenario("2024-01-03", "2024-01-05"))

    # A: +10%, -10%; B: 0%, +10% -> portfolio +5%, 0%.
    daily = np.array([0.05, 0.0])
    assert result.available
    assert result.n_returns == 2
    assert result.cumulative_return == pytest.approx(0.05)
    assert result.max_drawdown == pytest.approx(0.0)
    vol = np.std(daily, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    assert result.annualized_volatility == pytest.approx(vol)


def test_drawdown_is_peak_to_trough_inside_the_window() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"])
    single = pd.DataFrame({"A": [200.0, 100.0, 120.0, 90.0, 130.0]}, index=dates)

    result = stress_test(single, [1.0], WINDOW)

    # The 200 close before the window is not a peak; 120 -> 90 is.
    assert result.cumulative_return == pytest.approx(0.30)
    assert result.max_drawdown == pytest.approx(-0.25)


@pytest.mark.parametrize(("weights", "ratio"), [([1.0, 0.0], 99 / 100), ([0.0, 1.0], 44 / 50)])
def test_single_asset_return_is_its_price_ratio(weights: list[float], ratio: float) -> None:
    result = stress_test(prices(), weights, WINDOW)

    assert result.cumulative_return == pytest.approx(ratio - 1.0)


def test_reordering_assets_with_their_weights_changes_nothing() -> None:
    original = stress_test(prices(), [0.3, 0.7], WINDOW)
    swapped = stress_test(prices()[["B", "A"]], [0.7, 0.3], WINDOW)

    assert swapped.cumulative_return == pytest.approx(original.cumulative_return, abs=1e-15)
    assert swapped.max_drawdown == pytest.approx(original.max_drawdown, abs=1e-15)
    assert swapped.annualized_volatility == pytest.approx(original.annualized_volatility)
    assert swapped.n_returns == original.n_returns


def test_every_short_asset_is_named_in_column_order() -> None:
    history = prices().assign(C=[np.nan] * 5)
    history.loc[:"2024-01-04", "A"] = np.nan
    history.loc["2024-01-05":, "B"] = np.nan  # two missing weekdays; one would be a holiday

    result = stress_test(history, [0.4, 0.4, 0.2], WINDOW)

    assert not result.available
    assert result.reason == (
        "Insufficient history: A history starts 2024-01-05, after the scenario start "
        "2024-01-03; B history ends 2024-01-04, before the scenario end 2024-01-08; "
        "C has no price data."
    )
