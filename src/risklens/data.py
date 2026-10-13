"""Download historical prices and convert them to returns.

This is the only module in ``risklens`` that touches the network.
"""

from collections.abc import Sequence
from datetime import date

import pandas as pd
import yfinance as yf

from risklens.validation import validate_date_range, validate_prices


class DataFetchError(RuntimeError):
    """Raised when price data cannot be downloaded or is incomplete."""


def _close_prices(raw: object, tickers: list[str]) -> pd.DataFrame:
    """Extract the adjusted Close table from a ``yf.download`` response.

    Raises:
        DataFetchError: if the response is empty or not shaped like Yahoo data.
    """
    if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
        raise DataFetchError("No price data returned for the requested range.")
    if not isinstance(raw, pd.DataFrame):
        raise DataFetchError("Unexpected price response from Yahoo Finance.")
    try:
        close = raw["Close"]
    except KeyError as exc:
        raise DataFetchError("Price response has no Close prices.") from exc

    if isinstance(close, pd.Series):  # older yfinance flattens single tickers
        if len(tickers) != 1:
            raise DataFetchError("Price response has one Close column for several tickers.")
        close = close.to_frame(name=tickers[0])
    if not isinstance(close, pd.DataFrame) or not close.columns.is_unique:
        raise DataFetchError("Price response has repeated or malformed ticker columns.")
    return close


def fetch_prices(
    tickers: Sequence[str],
    start: str | date,
    end: str | date | None = None,
) -> pd.DataFrame:
    """Return daily adjusted close prices, one column per ticker.

    Columns follow the order of ``tickers``. Rows where any ticker is missing
    a price are dropped so every row is comparable across assets.

    Raises:
        ValueError: if ``tickers`` is empty or the dates fail
            ``validate_date_range``.
        DataFetchError: if the download fails, is empty or malformed, a ticker
            has no data, or the prices are not finite positive numbers.
    """
    tickers = list(tickers)
    if not tickers:
        raise ValueError("Enter at least one ticker.")
    validate_date_range(start, end)
    try:
        raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    except Exception as exc:  # yfinance raises many unrelated exception types
        raise DataFetchError(f"Price download failed: {exc}") from exc

    close = _close_prices(raw, tickers)
    missing = [t for t in tickers if t not in close.columns or close[t].isna().all()]
    if missing:
        raise DataFetchError(f"No price data for: {', '.join(missing)}.")

    prices = close[tickers].dropna()
    if len(prices) < 2:
        raise DataFetchError("Not enough overlapping price history to compute returns.")
    try:
        return validate_prices(prices)
    except ValueError as exc:
        raise DataFetchError(f"Downloaded prices are unusable: {exc}") from exc


BENCHMARK_TICKER = "SPY"  # SPDR S&P 500 ETF, a tradable S&P 500 proxy


def fetch_benchmark_prices(
    start: str | date,
    end: str | date | None = None,
) -> pd.Series:
    """Return daily adjusted close prices for the S&P 500 benchmark (SPY).

    Raises:
        DataFetchError: if the download fails or returns too little data.
    """
    return fetch_prices([BENCHMARK_TICKER], start, end)[BENCHMARK_TICKER]


def to_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Return simple daily returns (fractions) from adjusted prices.

    Accepts a price DataFrame (one column per asset) or a single price Series
    and returns the same shape, one row shorter.

    Raises:
        ValueError: if prices are not dated, sorted, finite, and positive
            (see ``validate_prices``), so no return is NaN or infinite.
    """
    frame = prices.to_frame() if isinstance(prices, pd.Series) else prices
    validate_prices(frame)
    return prices.astype(float).pct_change().dropna(how="all")
