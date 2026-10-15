"""Unit tests for price download errors and return conversion (no network)."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from risklens.data import DataFetchError, fetch_prices, to_returns


def dates(n: int) -> pd.DatetimeIndex:
    return pd.bdate_range("2024-01-02", periods=n)


def yahoo(close: dict[str, list[object]]) -> pd.DataFrame:
    """A ``yf.download`` style frame with ("Close", ticker) columns."""
    frame = pd.DataFrame(close, index=dates(len(next(iter(close.values())))))
    return pd.concat({"Close": frame}, axis=1)


def fetch(response: object, tickers: list[str]) -> pd.DataFrame:
    with patch("yfinance.download", return_value=response):
        return fetch_prices(tickers, "2024-01-01", "2024-02-01")


def test_returns_adjusted_close_in_ticker_order() -> None:
    raw = yahoo({"MSFT": [10.0, 11.0, 12.0], "AAPL": [1.0, 2.0, 3.0]})

    with patch("yfinance.download", return_value=raw) as download:
        result = fetch_prices(["AAPL", "MSFT"], "2024-01-01")

    assert download.call_args.kwargs["auto_adjust"] is True
    assert list(result.columns) == ["AAPL", "MSFT"]
    assert result.index.equals(dates(3))


def test_flat_single_ticker_response_is_named_after_ticker() -> None:
    raw = pd.DataFrame({"Close": [1.0, 2.0]}, index=dates(2))

    assert list(fetch(raw, ["AAPL"]).columns) == ["AAPL"]


def test_drops_dates_missing_for_any_ticker() -> None:
    raw = yahoo({"A": [1.0, np.nan, 3.0, 4.0], "B": [5.0, 6.0, 7.0, 8.0]})

    result = fetch(raw, ["A", "B"])

    assert result.index.equals(dates(4)[[0, 2, 3]])


def test_download_exception_becomes_data_fetch_error() -> None:
    with patch("yfinance.download", side_effect=RuntimeError("timeout")):
        with pytest.raises(DataFetchError, match="download failed: timeout"):
            fetch_prices(["A"], "2024-01-01")


@pytest.mark.parametrize(
    ("response", "tickers", "message"),
    [
        (None, ["A"], "No price data returned"),
        (pd.DataFrame(), ["A"], "No price data returned"),
        ([1.0, 2.0], ["A"], "Unexpected price response"),
        (
            pd.concat({"Open": pd.DataFrame({"A": [1.0, 2.0]}, index=dates(2))}, axis=1),
            ["A"],
            "no Close prices",
        ),
        (
            pd.DataFrame({"Close": [1.0, 2.0]}, index=dates(2)),
            ["A", "B"],
            "one Close column for several",
        ),
        (
            pd.concat(
                {
                    "Close": pd.DataFrame(
                        [[1.0, 2.0], [1.0, 2.0]], columns=["A", "A"], index=dates(2)
                    )
                },
                axis=1,
            ),
            ["A"],
            "repeated or malformed",
        ),
        (yahoo({"A": [1.0, 2.0], "B": [np.nan, np.nan]}), ["A", "B"], "No price data for: B"),
        (yahoo({"A": [1.0, 2.0]}), ["A", "C"], "No price data for: C"),
        (yahoo({"A": [1.0, np.nan], "B": [np.nan, 2.0]}), ["A", "B"], "overlapping"),
        (yahoo({"A": [1.0, 0.0, 2.0]}), ["A"], "positive"),
        (yahoo({"A": [1.0, np.inf, 2.0]}), ["A"], "missing or infinite"),
        (yahoo({"A": ["1.0", "x", "2.0"]}), ["A"], "must be numbers"),
    ],
)
def test_malformed_or_invalid_responses_raise_data_fetch_error(
    response: object, tickers: list[str], message: str
) -> None:
    with pytest.raises(DataFetchError, match=message):
        fetch(response, tickers)


def test_unsorted_dates_raise_data_fetch_error() -> None:
    raw = yahoo({"A": [1.0, 2.0, 3.0]}).iloc[::-1]

    with pytest.raises(DataFetchError, match="sorted and unique"):
        fetch(raw, ["A"])


def test_empty_ticker_list_is_rejected_before_download() -> None:
    with patch("yfinance.download") as download:
        with pytest.raises(ValueError, match="at least one ticker"):
            fetch_prices([], "2024-01-01")
    download.assert_not_called()


def test_to_returns_computes_simple_returns_for_frames_and_series() -> None:
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0]}, index=dates(3))

    frame = to_returns(prices)
    series = to_returns(prices["A"])

    np.testing.assert_allclose(frame["A"], [0.10, -0.10])
    assert frame.index.equals(dates(3)[1:])
    pd.testing.assert_series_equal(series, frame["A"])


@pytest.mark.parametrize(
    ("values", "message"),
    [([1.0, 0.0, 2.0], "positive"), ([1.0, np.nan, 2.0], "missing or infinite")],
)
def test_to_returns_rejects_prices_that_give_nonfinite_returns(
    values: list[float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        to_returns(pd.DataFrame({"A": values}, index=dates(3)))


def test_bad_date_range_is_rejected_before_download() -> None:
    with patch("yfinance.download") as download:
        with pytest.raises(ValueError, match="before"):
            fetch_prices(["A"], "2024-02-01", "2024-01-02")
    download.assert_not_called()
