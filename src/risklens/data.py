"""Download historical prices and convert them to returns.

This is the only module in ``risklens`` that touches the network.
"""

from collections.abc import Sequence
from datetime import date

import pandas as pd
import yfinance as yf


class DataFetchError(RuntimeError):
    """Raised when price data cannot be downloaded or is incomplete."""


def fetch_prices(
    tickers: Sequence[str],
    start: str | date,
    end: str | date | None = None,
) -> pd.DataFrame:
    """Return daily adjusted close prices, one column per ticker.

    Columns follow the order of ``tickers``. Rows where any ticker is missing
    a price are dropped so every row is comparable across assets.

    Raises:
        DataFetchError: if the download fails, is empty, or a ticker has no data.
    """
    tickers = list(tickers)
    try:
        raw = yf.download(
            tickers, start=start, end=end, auto_adjust=True, progress=False
        )
    except Exception as exc:  # yfinance raises many unrelated exception types
        raise DataFetchError(f"Price download failed: {exc}") from exc

    if raw is None or raw.empty:
        raise DataFetchError("No price data returned for the requested range.")

    close = raw["Close"]
    if isinstance(close, pd.Series):  # older yfinance flattens single tickers
        close = close.to_frame(name=tickers[0])

    missing = [t for t in tickers if t not in close.columns or close[t].isna().all()]
    if missing:
        raise DataFetchError(f"No price data for: {', '.join(missing)}.")

    prices = close[tickers].dropna()
    if len(prices) < 2:
        raise DataFetchError("Not enough overlapping price history to compute returns.")
    return prices


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


def to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Return simple daily returns (fractions) from a price DataFrame."""
    return prices.pct_change().dropna(how="all")
