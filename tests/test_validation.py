"""Unit tests for ticker, weight, risk-free rate, and price validation."""

import numpy as np
import pandas as pd
import pytest

from risklens.validation import (
    MAX_TICKERS,
    validate_prices,
    validate_risk_free_rate,
    validate_tickers,
    validate_weights,
)


def prices(values: dict[str, list[object]]) -> pd.DataFrame:
    n = len(next(iter(values.values())))
    return pd.DataFrame(values, index=pd.bdate_range("2024-01-02", periods=n))


def test_tickers_are_split_uppercased_and_deduplicated_in_order() -> None:
    assert validate_tickers(" aapl, msft  AAPL,spy ") == ["AAPL", "MSFT", "SPY"]
    assert validate_tickers(["brk-b", " ^gspc ", "eurusd=x", "es=f"]) == [
        "BRK-B",
        "^GSPC",
        "EURUSD=X",
        "ES=F",
    ]


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("", "at least one ticker"),
        (" , ", "at least one ticker"),
        (None, "text or a list"),
        (["AAPL", 5], "must be text"),
        ("AAPL, $$$", "Invalid ticker"),
        (",".join(f"T{i}" for i in range(MAX_TICKERS + 1)), "Too many tickers"),
    ],
)
def test_tickers_reject_bad_input(raw: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_tickers(raw)  # type: ignore[arg-type]


def test_weights_accept_ints_and_numpy_and_return_floats() -> None:
    result = validate_weights(np.array([1, 0]), 2)

    assert result.dtype == float
    np.testing.assert_array_equal(result, [1.0, 0.0])


@pytest.mark.parametrize(
    ("weights", "n_assets", "message"),
    [
        (["0.5", "0.5"], 2, "must be numbers"),
        ([True], 1, "must be numbers"),
        ([0.5, None], 2, "must be numbers"),
        ([[1.0]], 1, "flat list"),
        ([[0.5], [0.25, 0.25]], 2, "flat list"),
        ([0.5, 0.5], 3, "Expected 3"),
        ([np.inf, 0.0], 2, "finite"),
        ([1.5, -0.5], 2, "negative"),
        ([0.3333, 0.3333, 0.3333], 3, "sum to 1"),
    ],
)
def test_weights_reject_bad_input(weights: object, n_assets: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_weights(weights, n_assets)  # type: ignore[arg-type]


def test_weights_allow_float_rounding_within_tolerance() -> None:
    validate_weights([0.1, 0.2, 0.7 + 1e-9], 3)


@pytest.mark.parametrize("rate", [0, 0.04, -0.005, np.float32(0.02), 1.0])
def test_risk_free_rate_accepts_annual_fractions(rate: float) -> None:
    assert validate_risk_free_rate(rate) == pytest.approx(float(rate))


@pytest.mark.parametrize(
    ("rate", "message"),
    [
        ("0.04", "must be a number"),
        (True, "must be a number"),
        (None, "must be a number"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (4.0, "annual fraction"),
    ],
)
def test_risk_free_rate_rejects_bad_input(rate: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_risk_free_rate(rate)  # type: ignore[arg-type]


def test_prices_return_float_copy_without_mutating_input() -> None:
    raw = prices({"A": [1, 2, 3]})
    before = raw.copy()

    result = validate_prices(raw)

    assert result.dtypes.tolist() == [np.dtype(float)]
    assert result is not raw
    pd.testing.assert_frame_equal(raw, before)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ([[1.0, 2.0]], "pandas DataFrame"),
        (pd.DataFrame(index=pd.bdate_range("2024-01-02", periods=2)), "at least one asset"),
        (
            pd.DataFrame(
                [[1.0, 2.0], [1.0, 2.0]],
                columns=["A", "A"],
                index=pd.bdate_range("2024-01-02", periods=2),
            ),
            "unique",
        ),
        (pd.DataFrame({"A": [1.0, 2.0]}), "indexed by date"),
        (prices({"A": [1.0, 2.0]}).iloc[::-1], "sorted and unique"),
        (prices({"A": [1.0]}), "at least 2 price dates"),
        (prices({"A": ["1", "2"]}), "must be numbers"),
        (prices({"A": [True, True]}), "must be numbers"),
        (prices({"A": [1.0, np.nan]}), "missing or infinite"),
        (prices({"A": [1.0, np.inf]}), "missing or infinite"),
        (prices({"A": [1.0, 0.0]}), "positive"),
        (prices({"A": [1.0, -2.0]}), "positive"),
    ],
)
def test_prices_reject_bad_input(raw: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_prices(raw)  # type: ignore[arg-type]


def test_prices_honour_min_rows() -> None:
    with pytest.raises(ValueError, match="at least 3 price dates"):
        validate_prices(prices({"A": [1.0, 2.0]}), min_rows=3)


def test_date_range_parses_strings_and_dates() -> None:
    from datetime import date

    from risklens.validation import validate_date_range

    assert validate_date_range("2024-01-02", date(2024, 2, 1)) == (
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-02-01"),
    )
    assert validate_date_range(date(2024, 1, 2)) == (pd.Timestamp("2024-01-02"), None)


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("not a date", None, "valid date"),
        (None, "2024-01-02", "valid date"),
        ("2024-01-02", "31/31/2024", "valid date"),
        ("2024-02-01", "2024-01-02", "before"),
        ("2024-01-02", "2024-01-02", "before"),
        ("2999-01-01", None, "future"),
    ],
)
def test_date_range_rejects_bad_input(start: object, end: object, message: str) -> None:
    from risklens.validation import validate_date_range

    with pytest.raises(ValueError, match=message):
        validate_date_range(start, end)  # type: ignore[arg-type]
