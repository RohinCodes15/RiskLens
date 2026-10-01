"""Normal and Cornish-Fisher VaR, rolling VaR forecasts, and VaR backtests."""

import statistics

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import cornish_fisher_var, historical_var, normal_var

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
