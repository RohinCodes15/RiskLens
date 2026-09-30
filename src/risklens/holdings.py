"""Turn holdings entered as share counts or dollar values into portfolio weights.

Holdings come from the dashboard's inputs or from a CSV file with a
``ticker`` column and either a ``shares`` or a ``value`` (dollars) column.

All functions raise ``ValueError`` with a message suitable for showing in the UI.
"""

import csv
import io
import re

import numpy as np
import pandas as pd

from risklens.validation import MAX_TICKERS, validate_tickers

HOLDING_KINDS = ("shares", "value")  # share counts, or market values in dollars
# Thousands separators such as "1,250.50"; "1,5" is rejected rather than read as 15.
_THOUSANDS_PATTERN = re.compile(r"\d{1,3}(,\d{3})+(\.\d*)?")
_MAX_HEADER_ECHO = 80  # characters of a bad header repeated in the error message


def parse_holdings_csv(content: bytes | str) -> tuple[str, pd.Series]:
    """Return ``(kind, amounts)`` read from CSV text with one holding per row.

    The header row (any letter case) must contain ``ticker`` and exactly one
    of ``shares`` or ``value``; that column's name is ``kind``. Other columns
    are ignored and blank lines are skipped. ``amounts`` holds share counts,
    or market values in dollars, indexed by upper-case ticker in file order.
    Amounts may have a leading "$" and thousands separators ("$1,250.50").

    Raises:
        ValueError: if the file is not UTF-8 CSV text, the header is wrong,
            there are no rows or more than ``MAX_TICKERS``, or a row has a
            missing, invalid, or repeated ticker or an amount that is not a
            finite number of zero or more. Every bad row is listed by line.
    """
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8-sig")  # Excel starts files with a byte-order mark
        except UnicodeDecodeError as exc:
            raise ValueError("The holdings file must be UTF-8 CSV text.") from exc
    reader = csv.reader(io.StringIO(content))
    try:
        rows = [(reader.line_num, row) for row in reader if any(cell.strip() for cell in row)]
    except csv.Error as exc:
        raise ValueError(f"The holdings file is not valid CSV: {exc}.") from exc
    if not rows:
        raise ValueError("The holdings file is empty.")

    (_, header), body = rows[0], rows[1:]
    columns = [cell.strip().lower() for cell in header]
    kinds = [kind for kind in HOLDING_KINDS if kind in columns]
    if "ticker" not in columns or len(kinds) != 1:
        found = ",".join(header)[:_MAX_HEADER_ECHO]
        raise ValueError(
            "The first row must name a ticker column and either a shares or a value "
            f"column, like 'ticker,shares'; found '{found}'."
        )
    if not body:
        raise ValueError("The holdings file has no rows below the header.")
    if len(body) > MAX_TICKERS:
        raise ValueError(f"Too many holdings ({len(body)}); the limit is {MAX_TICKERS}.")

    kind = kinds[0]
    ticker_at, amount_at = columns.index("ticker"), columns.index(kind)
    amounts: dict[str, float] = {}
    first_lines: dict[str, int] = {}
    errors = []
    for line, row in body:
        cells = [*row, *[""] * (max(ticker_at, amount_at) + 1 - len(row))]  # pad short rows
        try:
            ticker, amount = _parse_row(cells[ticker_at], cells[amount_at], kind)
            if ticker in first_lines:
                raise ValueError(f"{ticker} is already listed on line {first_lines[ticker]}.")
        except ValueError as exc:
            errors.append(f"Line {line}: {exc}")
        else:
            first_lines[ticker] = line
            amounts[ticker] = amount
    if errors:
        raise ValueError(" ".join(errors))
    return kind, pd.Series(amounts, dtype=float, name=kind)


def _parse_row(ticker_text: str, amount_text: str, kind: str) -> tuple[str, float]:
    """Return one row's upper-case ticker and amount, raising for its first problem."""
    if not ticker_text.strip():
        raise ValueError("Ticker is missing.")
    [ticker] = validate_tickers([ticker_text])
    text = amount_text.strip().removeprefix("$")
    if not text:
        raise ValueError(f"{kind.capitalize()} is missing.")
    if _THOUSANDS_PATTERN.fullmatch(text):
        text = text.replace(",", "")
    try:
        amount = float(text)
    except ValueError:
        raise ValueError(
            f"{kind.capitalize()} must be a number; got {amount_text.strip()!r}."
        ) from None
    if not np.isfinite(amount) or amount < 0:
        raise ValueError(
            f"{kind.capitalize()} must be a finite number of zero or more; "
            f"got {amount_text.strip()!r}."
        )
    return ticker, amount
