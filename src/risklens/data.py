"""Download historical prices and convert them to returns.

This is the only module in ``risklens`` that touches the network.
"""

import io
import re
import zipfile
from collections.abc import Sequence
from datetime import date
from urllib.request import urlopen

import pandas as pd
import yfinance as yf

from risklens.validation import validate_date_range, validate_price_history, validate_prices


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


def _download_close(tickers: list[str], start: str | date, end: str | date | None) -> pd.DataFrame:
    """Validate the request, download it, and return the raw adjusted Close table.

    Raises:
        ValueError: if ``tickers`` is empty or the dates fail ``validate_date_range``.
        DataFetchError: if the download fails or the response is malformed.
    """
    if not tickers:
        raise ValueError("Enter at least one ticker.")
    validate_date_range(start, end)
    try:
        raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    except Exception as exc:  # yfinance raises many unrelated exception types
        raise DataFetchError(f"Price download failed: {exc}") from exc
    return _close_prices(raw, tickers)


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
    close = _download_close(tickers, start, end)
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


def fetch_price_history(
    tickers: Sequence[str],
    start: str | date,
    end: str | date | None = None,
) -> pd.DataFrame:
    """Return daily adjusted close prices with each ticker's own date coverage.

    Unlike ``fetch_prices``, dates are not cut down to those shared by every
    ticker. The index is every date on which at least one ticker traded, and
    NaN marks a date a ticker has no price (before it listed, after it
    delisted, or a missing day). A ticker with no data at all in the range
    is kept as an all-NaN column. Prices are never filled or interpolated.
    Columns follow the order of ``tickers``. Use this when coverage matters,
    as in ``risklens.analytics.stress_test``.

    Raises:
        ValueError: if ``tickers`` is empty or the dates fail
            ``validate_date_range``.
        DataFetchError: if the download fails, is malformed, no ticker has
            any price, or an observed price is not a finite positive number.
    """
    tickers = list(tickers)
    close = _download_close(tickers, start, end)
    history = close.reindex(columns=tickers).dropna(how="all")
    if history.empty:
        raise DataFetchError(f"No price data for: {', '.join(tickers)}.")
    try:
        return validate_price_history(history)
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


FRENCH_LIBRARY = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FRENCH_FILES = ("F-F_Research_Data_Factors_daily_CSV.zip", "F-F_Momentum_Factor_daily_CSV.zip")
DOWNLOAD_TIMEOUT_SECONDS = 30
_FRENCH_ROW = re.compile(r"^\s*\d{8}\s*,")


def _parse_french_csv(text: str) -> pd.DataFrame:
    """Parse the first daily table of a Ken French CSV into fractions on a date index.

    Raises:
        DataFetchError: if the text has no dated rows or a value is not numeric.
    """
    lines = text.splitlines()
    first = next((i for i, line in enumerate(lines) if _FRENCH_ROW.match(line)), None)
    if first is None or first == 0:
        raise DataFetchError("Factor file has no daily data table.")
    end = next((i for i in range(first, len(lines)) if not _FRENCH_ROW.match(lines[i])), len(lines))
    columns = [name.strip() for name in lines[first - 1].split(",")[1:]]
    rows = [line.split(",") for line in lines[first:end]]
    try:
        values = [[float(v) / 100.0 for v in row[1:]] for row in rows]  # files are in percent
        index = pd.to_datetime([row[0].strip() for row in rows], format="%Y%m%d")
        return pd.DataFrame(values, index=index, columns=columns)
    except ValueError as exc:
        raise DataFetchError(f"Factor file is malformed: {exc}") from exc


def _download_french(name: str) -> str:
    """Download one zipped Ken French CSV and return its text."""
    try:
        with urlopen(FRENCH_LIBRARY + name, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        return archive.read(archive.namelist()[0]).decode("latin-1")
    except Exception as exc:  # network, HTTP, and zip errors all mean the same here
        raise DataFetchError(f"Factor download failed: {exc}") from exc


def fetch_factors(start: str | date, end: str | date | None = None) -> pd.DataFrame:
    """Return daily Fama-French 3 factors, momentum, and the risk-free rate.

    Columns are ``Mkt-RF``, ``SMB``, ``HML``, ``RF`` and ``Mom``, as daily
    fractions (not percent), on dates from ``start`` up to but excluding
    ``end``. The library publishes with a lag of a month or more.

    Raises:
        ValueError: if the dates fail ``validate_date_range``.
        DataFetchError: if a download fails, is malformed, or has no rows in range.
    """
    validate_date_range(start, end)
    factors = pd.concat(
        [_parse_french_csv(_download_french(name)) for name in FRENCH_FILES], axis=1, join="inner"
    )
    factors = factors.loc[pd.Timestamp(start) :]
    if end is not None:
        factors = factors.loc[factors.index < pd.Timestamp(end)]
    if factors.empty:
        raise DataFetchError("No factor data in the selected period yet.")
    return factors


UNKNOWN_LABEL = "Unknown"


def fetch_classifications(tickers: Sequence[str]) -> pd.DataFrame:
    """Return each ticker's Yahoo Finance sector and country.

    The result is indexed by ticker with ``sector`` and ``country`` columns.
    Funds have no sector on Yahoo, so they are labelled with their quote type
    (e.g. ``ETF``). A ticker whose profile cannot be loaded gets ``Unknown``.
    """
    rows = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info or {}
        except Exception:  # one missing profile should not hide the others
            info = {}
        rows[ticker] = {
            "sector": info.get("sector") or info.get("quoteType") or UNKNOWN_LABEL,
            "country": info.get("country") or UNKNOWN_LABEL,
        }
    return pd.DataFrame.from_dict(rows, orient="index")


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
