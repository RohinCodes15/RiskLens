"""Validate user-supplied tickers and portfolio weights.

All functions raise ``ValueError`` with a message suitable for showing in the UI.
"""

import re
from collections.abc import Iterable, Sequence

import numpy as np

MAX_TICKERS = 25
WEIGHT_SUM_TOLERANCE = 1e-6
# Letters/digits plus the separators Yahoo uses: BRK-B, BRK.B, ^GSPC, EURUSD=X.
_TICKER_PATTERN = re.compile(r"^\^?[A-Z0-9][A-Z0-9.\-]{0,9}(=X)?$")


def validate_tickers(raw: str | Iterable[str]) -> list[str]:
    """Return a clean, de-duplicated, upper-case list of tickers.

    Accepts a comma/space separated string ("aapl, msft") or an iterable of
    strings. Order of first appearance is preserved.
    """
    parts = re.split(r"[,\s]+", raw) if isinstance(raw, str) else list(raw)
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
      * exactly one weight per asset (``n_assets``)
      * every weight is a finite number (no NaN / inf)
      * no negative weights
      * weights sum to 1 within ``WEIGHT_SUM_TOLERANCE``

    Raises:
        ValueError: describing the first rule that is broken.
    """
    try:
        arr = np.asarray(weights, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Weights must be numbers.") from exc

    if arr.ndim != 1 or arr.size != n_assets:
        raise ValueError(f"Expected {n_assets} weight(s), got {arr.size}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError("Weights must be finite numbers.")
    if np.any(arr < 0):
        raise ValueError("Weights cannot be negative.")
    total = float(arr.sum())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"Weights must sum to 1 (got {total:.6f}).")
    return arr
