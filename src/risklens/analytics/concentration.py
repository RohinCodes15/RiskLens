"""Portfolio concentration and cross-asset correlation."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from risklens.validation import validate_weights

MIN_CORRELATION_ROWS = 2


def herfindahl_index(weights: Sequence[float]) -> float:
    """Herfindahl-Hirschman Index of portfolio weights: sum of squared weights.

    Weights are long-only fractions summing to 1. The result ranges from
    1/n (equal weights across n holdings) to 1.0 (a single holding).

    Raises:
        ValueError: if the weights are invalid (see ``validate_weights``).
    """
    w = validate_weights(weights, len(weights))
    return float(np.sum(w**2))


def effective_holdings(weights: Sequence[float]) -> float:
    """Effective number of holdings, 1 / HHI.

    Equal weights across n assets give n; concentration pulls it toward 1.
    Zero-weight assets do not count.
    """
    return 1.0 / herfindahl_index(weights)


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation of daily returns, one row and column per asset.

    Rows with a missing return for any asset are dropped first, so every
    pair is measured on the same dates. An asset with constant returns has
    undefined correlation and shows NaN in its row and column.

    Raises:
        ValueError: if ``returns`` is not a DataFrame, has no columns,
            contains infinite values, or has fewer than 2 complete rows.
    """
    if not isinstance(returns, pd.DataFrame):
        raise ValueError("returns must be a pandas DataFrame.")
    if returns.shape[1] == 0:
        raise ValueError("returns must have at least one asset column.")
    try:
        complete = returns.astype(float).dropna()
    except (TypeError, ValueError) as exc:
        raise ValueError("returns must be numbers.") from exc
    if np.isinf(complete.to_numpy()).any():
        raise ValueError("returns contain infinite values.")
    if len(complete) < MIN_CORRELATION_ROWS:
        raise ValueError(
            f"Need at least {MIN_CORRELATION_ROWS} dates with returns for every asset."
        )
    return complete.corr()
