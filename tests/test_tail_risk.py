"""Unit tests for historical VaR / CVaR (Expected Shortfall) at 95% and 99%."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    VAR_CONFIDENCE_LEVELS,
    historical_cvar,
    historical_var,
    tail_risk_summary,
)

# -10.0%, -9.9%, ..., +9.9%: 200 evenly spaced daily returns.
LADDER = [i / 1000 for i in range(-100, 100)]


def series(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=len(values)))


def test_cvar_averages_returns_at_or_below_var_threshold() -> None:
    # 5% quantile of 5 returns interpolates to -4.4%; only -5% is in the tail.
    returns = series([-0.05, -0.02, 0.0, 0.01, 0.03])

    assert historical_var(returns, 0.95) == pytest.approx(0.044)
    assert historical_cvar(returns, 0.95) == pytest.approx(0.05)


@pytest.mark.parametrize(
    ("confidence", "var", "cvar"),
    [
        (0.95, 0.09005, 0.0955),  # tail = -10.0% .. -9.1% (10 days)
        (0.99, 0.09801, 0.0995),  # tail = -10.0%, -9.9%
    ],
)
def test_var_and_cvar_on_ladder(confidence: float, var: float, cvar: float) -> None:
    returns = series(LADDER)

    assert historical_var(returns, confidence) == pytest.approx(var)
    assert historical_cvar(returns, confidence) == pytest.approx(cvar)


def test_cvar_is_never_below_var() -> None:
    returns = series(list(np.random.default_rng(7).normal(0.0005, 0.012, 500)))

    for confidence in VAR_CONFIDENCE_LEVELS:
        assert historical_cvar(returns, confidence) >= historical_var(returns, confidence)


def test_zero_volatility_gives_equal_var_and_cvar() -> None:
    returns = series([0.001] * 30)

    assert historical_var(returns, 0.99) == pytest.approx(-0.001)
    assert historical_cvar(returns, 0.99) == pytest.approx(-0.001)


def test_cvar_is_negative_when_every_day_gains() -> None:
    assert historical_cvar(series([0.01, 0.02, 0.03])) == pytest.approx(-0.01)


def test_cvar_does_not_mutate_input() -> None:
    returns = series([-0.05, -0.02, 0.0, 0.01, 0.03])
    original = returns.copy()

    historical_cvar(returns, 0.99)

    pd.testing.assert_series_equal(returns, original)


@pytest.mark.parametrize(
    ("returns", "message"),
    [
        (series([]), "No returns"),
        (series([0.01, np.nan]), "NaN or infinite"),
        ([0.01, 0.02], "pandas Series"),
    ],
)
def test_cvar_rejects_bad_returns(returns: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        historical_cvar(returns)  # type: ignore[arg-type]


@pytest.mark.parametrize("confidence", [0.0, 1.0, 95.0])
def test_cvar_rejects_bad_confidence(confidence: float) -> None:
    with pytest.raises(ValueError, match="confidence"):
        historical_cvar(series(LADDER), confidence)


def test_summary_defaults_to_95_and_99() -> None:
    result = tail_risk_summary(series(LADDER))

    assert list(result.index) == [0.95, 0.99]
    assert list(result.columns) == ["var", "cvar", "sufficient_sample"]
    assert result.loc[0.99, "var"] == pytest.approx(0.09801)
    assert result.loc[0.99, "cvar"] == pytest.approx(0.0995)
    assert result["sufficient_sample"].tolist() == [True, True]


@pytest.mark.parametrize(
    ("n_returns", "confidence", "sufficient"),
    [(19, 0.95, False), (20, 0.95, True), (99, 0.99, False), (100, 0.99, True)],
)
def test_summary_flags_small_samples(n_returns: int, confidence: float, sufficient: bool) -> None:
    result = tail_risk_summary(series(LADDER[:n_returns]), [confidence])

    assert bool(result.loc[confidence, "sufficient_sample"]) is sufficient


def test_summary_rejects_bad_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        tail_risk_summary(series(LADDER), [0.95, 1.0])


def test_summary_rejects_empty_returns() -> None:
    with pytest.raises(ValueError, match="No returns"):
        tail_risk_summary(series([]))
