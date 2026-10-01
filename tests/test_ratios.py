"""Sortino and Calmar ratios from simple daily returns."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics.metrics import (
    TRADING_DAYS_PER_YEAR,
    calmar_ratio,
    sharpe_ratio,
    sortino_ratio,
)

DAYS = TRADING_DAYS_PER_YEAR


def dated(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2026-01-05", periods=len(values)))


RETURNS = dated([0.01, -0.02, 0.03, -0.01])


def test_sortino_divides_annual_return_by_downside_deviation_over_all_days() -> None:
    # Shortfalls are -0.02 and -0.01; the two up days count as zero shortfall.
    downside = np.sqrt((0.02**2 + 0.01**2) / 4) * np.sqrt(DAYS)
    assert sortino_ratio(RETURNS) == pytest.approx(0.0025 * DAYS / downside)


def test_sortino_measures_shortfalls_below_the_daily_risk_free_rate() -> None:
    rate = 0.0252  # 0.0001 per day
    downside = np.sqrt((0.0201**2 + 0.0101**2) / 4) * np.sqrt(DAYS)
    assert sortino_ratio(RETURNS, rate) == pytest.approx((0.0025 * DAYS - rate) / downside)


def test_bigger_gains_raise_sortino_in_proportion_but_not_sharpe() -> None:
    calm = dated([0.02, -0.01, 0.02, -0.01])
    spiky = dated([0.06, -0.01, 0.06, -0.01])  # same losses, mean return five times higher
    assert sortino_ratio(spiky) / sortino_ratio(calm) == pytest.approx(5.0)
    assert sharpe_ratio(spiky) / sharpe_ratio(calm) < 5.0


@pytest.mark.parametrize("values", [[0.01, 0.02, 0.0], [0.0, 0.0, 0.0]])
def test_sortino_is_nan_without_any_shortfall(values: list[float]) -> None:
    assert np.isnan(sortino_ratio(dated(values)))


@pytest.mark.parametrize(
    ("returns", "rate", "message"),
    [
        (RETURNS, 4.0, "annual fraction"),
        (pd.Series(dtype=float), 0.0, "No returns"),
        (dated([0.01, float("nan")]), 0.0, "NaN"),
    ],
)
def test_sortino_rejects_invalid_input(returns: pd.Series, rate: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        sortino_ratio(returns, rate)


def test_calmar_divides_compound_annual_growth_by_the_worst_drawdown() -> None:
    # Wealth 1.01 -> 0.9898 (-2% from the peak) -> 1.0195 -> 1.0093 (-1%).
    growth = (1.01 * 0.98 * 1.03 * 0.99) ** (DAYS / 4) - 1
    assert calmar_ratio(RETURNS) == pytest.approx(growth / 0.02)


def test_calmar_is_negative_when_the_portfolio_lost_money() -> None:
    losing = dated([-0.05, 0.01, -0.02])
    assert calmar_ratio(losing) < 0


@pytest.mark.parametrize("values", [[0.01, 0.02, 0.0], [0.0, 0.0, 0.0]])
def test_calmar_is_nan_without_a_drawdown(values: list[float]) -> None:
    assert np.isnan(calmar_ratio(dated(values)))


def test_calmar_needs_dated_returns() -> None:
    with pytest.raises(ValueError, match="indexed by date"):
        calmar_ratio(pd.Series([0.01, -0.02]))
