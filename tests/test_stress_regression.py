"""Regression tests for stress-window boundaries and hand-checkable results."""

import numpy as np
import pytest
from test_stress import prices

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
