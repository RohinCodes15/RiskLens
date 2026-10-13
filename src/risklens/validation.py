"""Validate user-supplied tickers, weights, rates, dates, and price tables.

All functions raise ``ValueError`` with a message suitable for showing in the UI.
"""

import numbers
import re
from collections.abc import Iterable, Sequence
from datetime import date

import numpy as np
import pandas as pd

MAX_TICKERS = 25
WEIGHT_SUM_TOLERANCE = 1e-6
MIN_PRICE_ROWS = 2
# An annual rate above 100% is almost certainly a percent typed as a fraction.
MAX_ABS_RISK_FREE_RATE = 1.0
# Letters/digits plus the separators Yahoo uses: BRK-B, BRK.B, ^GSPC, EURUSD=X, ES=F.
_TICKER_PATTERN = re.compile(r"^\^?[A-Z0-9][A-Z0-9.\-]{0,9}(=[XF])?$")
_NUMERIC_KINDS = "iuf"  # numpy dtype kinds for int, unsigned int, float


def validate_tickers(raw: str | Iterable[str]) -> list[str]:
    """Return a clean, de-duplicated, upper-case list of tickers.

    Accepts a comma/space separated string ("aapl, msft") or an iterable of
    strings. Order of first appearance is preserved.
    """
    if isinstance(raw, str):
        parts = re.split(r"[,\s]+", raw)
    else:
        try:
            parts = list(raw)
        except TypeError as exc:
            raise ValueError("Tickers must be text or a list of text.") from exc
        if not all(isinstance(p, str) for p in parts):
            raise ValueError("Each ticker must be text.")
    tickers = list(dict.fromkeys(p.strip().upper() for p in parts if p and p.strip()))

    if not tickers:
        raise ValueError("Enter at least one ticker.")
    if len(tickers) > MAX_TICKERS:
        raise ValueError(f"Too many tickers ({len(tickers)}); the limit is {MAX_TICKERS}.")
    invalid = [t for t in tickers if not _TICKER_PATTERN.fullmatch(t)]
    if invalid:
        raise ValueError(f"Invalid ticker symbol(s): {', '.join(invalid)}.")
    return tickers


def validate_weights(weights: Sequence[float], n_assets: int) -> np.ndarray:
    """Return portfolio weights as a float array after checking they are usable.

    Rules (long-only portfolio, weights as fractions, not percents):
      * a flat sequence of real numbers (no text, booleans, or None)
      * exactly one weight per asset (``n_assets``)
      * every weight is a finite number (no NaN / inf)
      * no negative weights
      * weights sum to 1 within ``WEIGHT_SUM_TOLERANCE``

    Raises:
        ValueError: describing the first rule that is broken.
    """
    try:
        raw = np.asarray(weights)
    except (TypeError, ValueError) as exc:  # ragged nested lists
        raise ValueError("Weights must be a flat list of numbers.") from exc
    if raw.dtype.kind not in _NUMERIC_KINDS:
        raise ValueError("Weights must be numbers.")
    if raw.ndim != 1:
        raise ValueError("Weights must be a flat list of numbers.")
    arr = raw.astype(float)

    if arr.size != n_assets:
        raise ValueError(f"Expected {n_assets} weight(s), got {arr.size}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Weights must be finite numbers.")
    if np.any(arr < 0):
        raise ValueError("Weights cannot be negative.")
    total = float(arr.sum())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"Weights must sum to 1 (got {total:.6f}).")
    return arr


def validate_risk_free_rate(rate: float) -> float:
    """Return an annual risk-free rate as a float fraction (0.04 == 4%).

    Raises:
        ValueError: if the rate is not a real number, is NaN/inf, or its
            magnitude exceeds ``MAX_ABS_RISK_FREE_RATE`` (likely a percent).
    """
    if isinstance(rate, (bool, np.bool_)) or not isinstance(rate, numbers.Real):
        raise ValueError("Risk-free rate must be a number.")
    value = float(rate)
    if not np.isfinite(value):
        raise ValueError("Risk-free rate must be a finite number.")
    if abs(value) > MAX_ABS_RISK_FREE_RATE:
        raise ValueError(f"Risk-free rate must be an annual fraction (0.04 for 4%); got {value}.")
    return value


def validate_prices(prices: pd.DataFrame, min_rows: int = MIN_PRICE_ROWS) -> pd.DataFrame:
    """Return a float copy of a price table after checking it is usable.

    Rules: a DataFrame with at least one uniquely named asset column, a
    sorted and unique ``DatetimeIndex``, at least ``min_rows`` dates, numeric
    (non-boolean) columns, and only finite, strictly positive prices.

    Raises:
        ValueError: describing the first rule that is broken.
    """
    if not isinstance(prices, pd.DataFrame):
        raise ValueError("Prices must be a pandas DataFrame.")
    if prices.shape[1] == 0:
        raise ValueError("Prices must have at least one asset column.")
    if not prices.columns.is_unique:
        raise ValueError("Price columns must be unique.")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Prices must be indexed by date.")
    if not (prices.index.is_monotonic_increasing and prices.index.is_unique):
        raise ValueError("Price dates must be sorted and unique.")
    if len(prices) < min_rows:
        raise ValueError(f"Need at least {min_rows} price dates; got {len(prices)}.")
    if not all(
        pd.api.types.is_numeric_dtype(t) and not pd.api.types.is_bool_dtype(t)
        for t in prices.dtypes
    ):
        raise ValueError("Prices must be numbers.")
    values = prices.to_numpy(dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("Prices contain missing or infinite values.")
    if np.any(values <= 0):
        raise ValueError("Prices must be positive.")
    return prices.astype(float)


def validate_date_range(
    start: str | date, end: str | date | None = None
) -> tuple[pd.Timestamp, pd.Timestamp | None]:
    """Return ``(start, end)`` as timestamps after checking they form a range.

    ``end`` is optional (``None`` means "up to today"). Rules: both parse as
    dates ("2024-01-31", ``date`` objects), neither is missing (NaT), the
    start is strictly before the end, and the start is not in the future.

    Raises:
        ValueError: describing the first rule that is broken.
    """
    start_ts = _parse_date(start, "start")
    end_ts = None if end is None else _parse_date(end, "end")
    try:
        if end_ts is not None and start_ts >= end_ts:
            raise ValueError("The start date must be before the end date.")
    except TypeError as exc:  # one date has a time zone and the other does not
        raise ValueError("Start and end dates must both have, or both lack, a time zone.") from exc
    naive_start = start_ts.tz_localize(None) if start_ts.tz else start_ts
    if naive_start.normalize() > pd.Timestamp.today().normalize():
        raise ValueError("The start date cannot be in the future.")
    return start_ts, end_ts


def _parse_date(value: str | date, label: str) -> pd.Timestamp:
    """Parse ``value`` as a timestamp, rejecting missing or unparseable dates."""
    try:
        stamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"The {label} date is not a valid date: {value!r}.") from exc
    if pd.isna(stamp):
        raise ValueError(f"The {label} date is not a valid date: {value!r}.")
    return stamp
