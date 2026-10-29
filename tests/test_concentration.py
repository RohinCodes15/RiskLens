"""Unit tests for concentration metrics and the correlation matrix."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import correlation_matrix, effective_holdings, herfindahl_index


def test_equal_weights_give_minimum_hhi_and_n_holdings() -> None:
    weights = [0.25, 0.25, 0.25, 0.25]

    assert herfindahl_index(weights) == pytest.approx(0.25)
    assert effective_holdings(weights) == pytest.approx(4.0)


def test_single_holding_is_fully_concentrated() -> None:
    assert herfindahl_index([1.0]) == pytest.approx(1.0)
    assert effective_holdings([1.0, 0.0, 0.0]) == pytest.approx(1.0)


def test_uneven_weights() -> None:
    weights = [0.5, 0.3, 0.2]

    assert herfindahl_index(weights) == pytest.approx(0.38)
    assert effective_holdings(weights) == pytest.approx(1 / 0.38)


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        ([], "sum to 1"),
        ([0.5, 0.4], "sum to 1"),
        ([1.2, -0.2], "negative"),
        ([np.nan, 1.0], "finite"),
    ],
)
def test_concentration_rejects_invalid_weights(weights: list[float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        herfindahl_index(weights)


def test_correlation_matrix_is_symmetric_with_unit_diagonal() -> None:
    returns = pd.DataFrame(
        {"A": [0.01, -0.02, 0.03, 0.00], "B": [0.02, -0.04, 0.06, 0.00], "C": [-0.01, 0.02, -0.03, 0.0]}
    )

    result = correlation_matrix(returns)

    assert list(result.columns) == ["A", "B", "C"]
    np.testing.assert_allclose(np.diag(result), 1.0)
    assert result.loc["A", "B"] == pytest.approx(1.0)
    assert result.loc["A", "C"] == pytest.approx(-1.0)
    pd.testing.assert_frame_equal(result, result.T)


def test_correlation_drops_rows_with_missing_returns() -> None:
    returns = pd.DataFrame({"A": [0.01, np.nan, 0.03, 0.02], "B": [0.01, 0.05, 0.03, 0.02]})

    result = correlation_matrix(returns)

    expected = returns.dropna().corr()
    pd.testing.assert_frame_equal(result, expected)


def test_constant_asset_has_nan_correlation() -> None:
    returns = pd.DataFrame({"A": [0.01, 0.02, 0.03], "B": [0.0, 0.0, 0.0]})

    result = correlation_matrix(returns)

    assert np.isnan(result.loc["A", "B"])


@pytest.mark.parametrize(
    ("returns", "message"),
    [
        ([[0.01, 0.02]], "pandas DataFrame"),
        (pd.DataFrame(index=range(3)), "at least one asset"),
        (pd.DataFrame({"A": [0.01, np.nan], "B": [0.02, 0.03]}), "at least 2 dates"),
        (pd.DataFrame({"A": [0.01, np.inf], "B": [0.02, 0.03]}), "infinite"),
    ],
)
def test_correlation_rejects_invalid_input(returns: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        correlation_matrix(returns)  # type: ignore[arg-type]
