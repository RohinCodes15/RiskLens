"""A day dropped from a stress window merges returns; it does not remove one."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import custom_scenario, stress_test


def test_dropped_day_merges_two_returns_into_one_observation() -> None:
    """The return across the gap compounds both days and counts once."""
    dates = pd.bdate_range("2021-01-04", periods=5)
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0, 104.0, 104.0]}, index=dates)
    gapped = prices.copy()
    gapped.iloc[3] = np.nan  # not the trough, so the drawdown is unchanged
    scenario = custom_scenario(dates[0], dates[-1])
    full, merged = stress_test(prices, [1.0], scenario), stress_test(gapped, [1.0], scenario)
    assert (full.n_returns, merged.n_returns) == (4, 3)
    assert merged.cumulative_return == pytest.approx(full.cumulative_return)
    assert merged.max_drawdown == pytest.approx(full.max_drawdown)
    assert full.max_drawdown == pytest.approx(99.0 / 110.0 - 1.0)
