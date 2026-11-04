"""Turnover limits: how much of the portfolio a suggested allocation may trade.

One-way turnover from weights ``a`` to ``b`` is ``0.5 × Σ|b − a|``: the share of
the portfolio bought, which equals the share sold. 0.25 means a quarter of
the portfolio changes hands; 1.0 means a complete swap.

The optimizer keeps that below a limit T with linear constraints only, so it
stays convex. With extra variables u_i ≥ |x_i − s·c_i|, where c are the
current weights and s = Σx (1 for fully invested weights, and the scale of
the rescaled maximum-Sharpe problem), the limit becomes Σu ≤ 2·T·s.
"""

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
