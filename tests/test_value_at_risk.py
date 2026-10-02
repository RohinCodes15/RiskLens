"""Normal and Cornish-Fisher VaR, rolling VaR forecasts, and VaR backtests."""

import math
import statistics

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    KUPIEC_SIGNIFICANCE,
    cornish_fisher_var,
    historical_var,
    kupiec_test,
    normal_var,
    rolling_var,
)

RETURNS = pd.Series(
    [0.012, -0.021, 0.004, 0.017, -0.035, 0.009, -0.006, 0.002, 0.011, -0.014],
    index=pd.bdate_range("2026-01-05", periods=10),
)


def test_normal_var_is_minus_the_normal_quantile_of_mean_and_sample_std() -> None:
    sample = list(RETURNS)
    quantile = statistics.NormalDist(statistics.fmean(sample), statistics.stdev(sample))
    assert normal_var(RETURNS, 0.95) == pytest.approx(-quantile.inv_cdf(0.05))
    assert normal_var(RETURNS, 0.99) == pytest.approx(-quantile.inv_cdf(0.01))


def test_cornish_fisher_adjusts_the_normal_quantile_for_pandas_skew_and_kurtosis() -> None:
    z = statistics.NormalDist().inv_cdf(0.05)
    s, k = RETURNS.skew(), RETURNS.kurt()
    adjusted = z + (z**2 - 1) * s / 6 + (z**3 - 3 * z) * k / 24 - (2 * z**3 - 5 * z) * s**2 / 36
    expected = -(RETURNS.mean() + adjusted * RETURNS.std())
    assert cornish_fisher_var(RETURNS, 0.95) == pytest.approx(expected)


def test_a_fat_left_tail_raises_cornish_fisher_above_normal_var() -> None:
    rng = np.random.default_rng(1)
    values = rng.normal(0.0005, 0.01, 500)
    values[::50] = -0.08  # ten crash days
    returns = pd.Series(values)
    assert cornish_fisher_var(returns, 0.99) > normal_var(returns, 0.99)


def test_both_models_match_historical_var_on_a_large_normal_sample() -> None:
    returns = pd.Series(np.random.default_rng(2).normal(0.0, 0.01, 200_000))
    historical = historical_var(returns, 0.95)
    assert normal_var(returns, 0.95) == pytest.approx(historical, rel=0.01)
    assert cornish_fisher_var(returns, 0.95) == pytest.approx(historical, rel=0.01)


@pytest.mark.parametrize("model", [normal_var, cornish_fisher_var])
def test_constant_returns_give_minus_the_return(model: object) -> None:
    assert model(pd.Series([0.001] * 20), 0.99) == pytest.approx(-0.001)


@pytest.mark.parametrize(
    ("model", "returns", "confidence", "message"),
    [
        (normal_var, RETURNS, 1.0, "between 0 and 1"),
        (cornish_fisher_var, RETURNS, 0.0, "between 0 and 1"),
        (normal_var, RETURNS.iloc[:1], 0.95, "at least 2"),
        (cornish_fisher_var, RETURNS.iloc[:3], 0.95, "at least 4"),
        (normal_var, pd.Series([0.01, float("nan")]), 0.95, "NaN"),
    ],
)
def test_models_reject_invalid_input(
    model: object, returns: pd.Series, confidence: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        model(returns, confidence)


def daily(count: int, seed: int = 3) -> pd.Series:
    values = np.random.default_rng(seed).standard_t(4, count) * 0.01
    return pd.Series(values, index=pd.bdate_range("2025-01-02", periods=count))


@pytest.mark.parametrize(
    ("method", "model"),
    [
        ("historical", historical_var),
        ("normal", normal_var),
        ("cornish_fisher", cornish_fisher_var),
    ],
)
def test_each_forecast_is_the_model_on_the_window_before_that_day(
    method: str, model: object
) -> None:
    returns = daily(80)
    forecasts = rolling_var(returns, 20, 0.95, method)
    assert forecasts.index.equals(returns.index[20:])
    for position in (20, 47, 79):
        expected = model(returns.iloc[position - 20 : position], 0.95)
        assert forecasts[returns.index[position]] == pytest.approx(expected)


def test_a_days_own_return_never_changes_its_forecast() -> None:
    returns = daily(40)
    shocked = returns.copy()
    shocked.iloc[30] = -0.5
    before, after = rolling_var(returns, 10), rolling_var(shocked, 10)
    pd.testing.assert_series_equal(before.loc[: returns.index[30]], after.loc[: returns.index[30]])
    assert after[returns.index[31]] > before[returns.index[31]]


@pytest.mark.parametrize(
    ("returns", "window", "method", "message"),
    [
        (daily(30), 10, "garch", "method must be one of"),
        (daily(30), 3, "normal", "at least 4"),
        (daily(30), 10.5, "normal", "whole number"),
        (daily(30), True, "normal", "whole number"),
        (daily(10), 10, "normal", "more than 10 daily returns"),
        (daily(30).reset_index(drop=True), 10, "normal", "indexed by date"),
    ],
)
def test_rolling_var_rejects_invalid_input(
    returns: pd.Series, window: object, method: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        rolling_var(returns, window, 0.95, method)


def chi_square_one_tail(statistic: float) -> float:
    """P(chi-square with 1 degree of freedom > statistic), without scipy."""
    return math.erfc(math.sqrt(statistic / 2))


def test_kupiec_statistic_and_p_value_match_the_likelihood_ratio_by_hand() -> None:
    # 10 breaches in 250 days against a 1% VaR (2.5 expected).
    by_hand = -2 * (
        240 * math.log(0.99) + 10 * math.log(0.01) - 240 * math.log(0.96) - 10 * math.log(0.04)
    )
    statistic, p_value = kupiec_test(10, 250, 0.99)
    assert statistic == pytest.approx(by_hand)
    assert p_value == pytest.approx(chi_square_one_tail(by_hand))
    assert p_value < KUPIEC_SIGNIFICANCE


@pytest.mark.parametrize(
    ("breaches", "statistic"),
    [(0, -2 * 255 * math.log(0.99)), (255, -2 * 255 * math.log(0.01))],
)
def test_kupiec_handles_no_breaches_and_all_breaches(breaches: int, statistic: float) -> None:
    assert kupiec_test(breaches, 255, 0.99)[0] == pytest.approx(statistic)


def test_kupiec_accepts_exactly_the_expected_breach_rate() -> None:
    assert kupiec_test(5, 100, 0.95) == pytest.approx((0.0, 1.0))


@pytest.mark.parametrize(
    ("confidence", "days", "accepted"),
    [(0.95, 255, (7, 20)), (0.99, 1000, (5, 16)), (0.95, 1000, (38, 64)), (0.90, 510, (39, 64))],
)
def test_kupiec_accepts_the_published_breach_ranges(
    confidence: float, days: int, accepted: tuple[int, int]
) -> None:
    # Non-rejection regions at 5% significance from Kupiec (1995) as tabulated
    # in Jorion, "Value at Risk".
    passing = [x for x in range(days + 1) if kupiec_test(x, days, confidence)[1] >= 0.05]
    assert passing == list(range(accepted[0], accepted[1] + 1))


@pytest.mark.parametrize(
    ("breaches", "days", "confidence", "message"),
    [
        (1, 0, 0.95, "days must be at least 1"),
        (5, 4, 0.95, "between 0 and 4"),
        (-1, 4, 0.95, "between 0 and 4"),
        (1.5, 4, 0.95, "breaches must be a whole number"),
        (1, True, 0.95, "days must be a whole number"),
        (1, 4, 1.5, "between 0 and 1"),
    ],
)
def test_kupiec_rejects_invalid_counts(
    breaches: object, days: object, confidence: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        kupiec_test(breaches, days, confidence)
