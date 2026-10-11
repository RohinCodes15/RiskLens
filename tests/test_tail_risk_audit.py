"""Input-validation edge cases for historical VaR, CVaR, and the tail summary."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import historical_cvar, historical_var, tail_risk_summary

RETURNS = pd.Series([0.01, -0.02, 0.03, -0.01, 0.0])


@pytest.mark.parametrize("func", [historical_var, historical_cvar])
@pytest.mark.parametrize("confidence", ["0.95", None, True, np.True_])
def test_non_numeric_confidence_raises_value_error(func: object, confidence: object) -> None:
    with pytest.raises(ValueError, match="number between 0 and 1"):
        func(RETURNS, confidence)  # type: ignore[operator]


@pytest.mark.parametrize("confidence", [np.float64(0.95), 0.99])
def test_numpy_and_python_floats_are_accepted(confidence: float) -> None:
    assert historical_cvar(RETURNS, confidence) >= historical_var(RETURNS, confidence)


def test_summary_rejects_returns_with_nan() -> None:
    with pytest.raises(ValueError, match="NaN"):
        tail_risk_summary(pd.Series([0.01, np.nan, -0.02]))


def test_exactly_one_tail_observation_counts_as_sufficient() -> None:
    returns = pd.Series(np.linspace(-0.05, 0.05, 100))

    summary = tail_risk_summary(returns)

    assert summary.loc[0.99, "sufficient_sample"]
    assert not tail_risk_summary(returns.iloc[:99]).loc[0.99, "sufficient_sample"]
