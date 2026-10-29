"""Unit tests for the dated drawdown series and max drawdown."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import drawdown_series, max_drawdown


def dated(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2024-01-02", periods=len(values)))


def test_first_day_loss_counts_against_initial_wealth() -> None:
    returns = dated([-0.10, 0.05])

    result = drawdown_series(returns)

    assert result.iloc[0] == pytest.approx(-0.10)
    assert result.iloc[1] == pytest.approx(0.90 * 1.05 - 1)


def test_tracks_peak_and_recovery_with_matching_dates() -> None:
    returns = dated([0.10, -0.20, 0.25, 0.0])

    result = drawdown_series(returns)

    assert result.index.equals(returns.index)
    assert result.name == "drawdown"
    np.testing.assert_allclose(result.to_numpy(), [0.0, -0.20, 0.0, 0.0], atol=1e-12)
    assert (result <= 0).all()


def test_max_drawdown_is_minimum_of_series() -> None:
    returns = dated([0.05, -0.10, -0.10, 0.30])

    assert max_drawdown(returns) == pytest.approx(drawdown_series(returns).min())
    assert max_drawdown(returns) == pytest.approx(0.9 * 0.9 - 1)


def test_does_not_mutate_input() -> None:
    returns = dated([0.01, -0.02])
    original = returns.copy()

    drawdown_series(returns)

    pd.testing.assert_series_equal(returns, original)


@pytest.mark.parametrize(
    ("returns", "message"),
    [
        (dated([]), "No returns"),
        (pd.Series([0.01, -0.02]), "indexed by date"),
        (dated([0.01, np.nan]), "NaN or infinite"),
        (dated([0.01, np.inf]), "NaN or infinite"),
        (dated([0.01, -1.5]), "below -100%"),
        (dated([0.01, 0.02]).iloc[::-1], "sorted and unique"),
        ([0.01, 0.02], "pandas Series"),
    ],
)
def test_rejects_invalid_input(returns: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        drawdown_series(returns)  # type: ignore[arg-type]
