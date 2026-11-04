"""Turnover limits: how much of the portfolio a suggested allocation may trade.

One-way turnover from weights ``a`` to ``b`` is ``0.5 × Σ|b − a|``: the share of
the portfolio bought, which equals the share sold. 0.25 means a quarter of
the portfolio changes hands; 1.0 means a complete swap.

The optimizer keeps that below a limit T with linear constraints only, so it
stays convex. With extra variables u_i ≥ |x_i − s·c_i|, where c are the
current weights and s = Σx (1 for fully invested weights, and the scale of
the rescaled maximum-Sharpe problem), the limit becomes Σu ≤ 2·T·s.
"""

import numbers
from collections.abc import Sequence

import numpy as np

from risklens.validation import validate_weights


def one_way_turnover(before: Sequence[float], after: Sequence[float]) -> float:
    """One-way turnover (a fraction, 0 to 1) to move from ``before`` to ``after`` weights.

    Raises:
        ValueError: if either is not a valid weight list of the same length.
    """
    start = validate_weights(before, len(before))
    end = validate_weights(after, len(start))
    return 0.5 * float(np.abs(end - start).sum())


def validate_turnover_limit(max_turnover: float) -> float:
    """Return ``max_turnover`` as a float if it is a number from 0 to 1.

    Raises:
        ValueError: if it is not a finite number in [0, 1].
    """
    if isinstance(max_turnover, (bool, np.bool_)) or not isinstance(max_turnover, numbers.Real):
        raise ValueError("max_turnover must be a number (0.2 for 20% of the portfolio).")
    value = float(max_turnover)
    if not np.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("max_turnover must be between 0 and 1.")
    return value


def turnover_constraints(current: np.ndarray, limit: float) -> np.ndarray:
    """Rows G with G @ [x, u] ≥ 0 for u ≥ |x − s·current| and Σu ≤ 2·limit·s, s = Σx.

    ``current`` holds the current weights (summing to 1) and ``limit`` the
    one-way turnover limit; the result has 2n + 1 rows and 2n columns.
    """
    n = len(current)
    scaled = np.outer(current, np.ones(n))  # row i of scaled @ x is current_i · Σx
    identity = np.eye(n)
    above = np.hstack([scaled - identity, identity])  # u − x + current·s ≥ 0
    below = np.hstack([identity - scaled, identity])  # u + x − current·s ≥ 0
    budget = np.concatenate([np.full(n, 2.0 * limit), -np.ones(n)])[None, :]
    return np.vstack([above, below, budget])
