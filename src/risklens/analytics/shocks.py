"""Custom shocks: estimate a portfolio's move when market proxies move by set amounts.

Method:
    1. Each shock is a move in a proxy ETF, e.g. technology (XLK) −20%.
    2. Every holding's daily returns are regressed by least squares on the
       daily returns of the shocked proxies only, over the dates they share.
    3. A holding's estimated move is its betas times the shocks, capped at
       −100% because a long position cannot lose more than its value.
    4. The portfolio's move is the weighted sum of the holdings' moves.

Proxies that are not shocked are left out of the regression, so a holding's
beta to technology also carries whatever moves with technology (such as the
broad market). This is the usual "if technology falls 20%, what happens to me"
reading. The estimate is linear and instantaneous, applies to today's target
weights, and is not a prediction.
"""

import numbers
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Proxy ETFs a user can shock, by display name.
SHOCK_PROXIES = {
    "Market": "SPY",
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Long-term bonds": "TLT",
    "Gold": "GLD",
}
MIN_SHOCK_OBS = 60  # about three months of shared trading days
MAX_LOSS = -1.0  # a long position cannot lose more than 100%


@dataclass(frozen=True)
class ShockImpact:
    """Estimated instantaneous effect of a set of proxy shocks. Moves are fractions.

    Attributes:
        portfolio_impact: estimated portfolio return under the shocks
            (−0.08 means an 8% loss); the sum of ``holdings["contribution"]``.
        holdings: indexed by ticker, with ``weight``, ``impact`` (the
            holding's estimated move), ``contribution`` (weight × impact),
            and ``r_squared`` (share of the holding's daily variance the
            shocked proxies explain; NaN for a constant holding).
        betas: holdings × shocked proxies, from the daily regression.
        shocks: the non-zero shocks used, by proxy name.
        observations / first_date / last_date: the shared dates used.
    """

    portfolio_impact: float
    holdings: pd.DataFrame
    betas: pd.DataFrame
    shocks: pd.Series
    observations: int
    first_date: pd.Timestamp
    last_date: pd.Timestamp


def _active_shocks(shocks: Mapping[str, float], proxies: pd.Index) -> pd.Series:
    """Return the non-zero shocks as a Series, after checking every value."""
    if not isinstance(shocks, Mapping):
        raise ValueError("Shocks must map proxy names to moves (e.g. {'Technology': -0.2}).")
    unknown = [name for name in shocks if name not in proxies]
    if unknown:
        raise ValueError(f"No returns for shocked proxy: {', '.join(map(str, unknown))}.")
    for name, move in shocks.items():
        if isinstance(move, (bool, np.bool_)) or not isinstance(move, numbers.Real):
            raise ValueError(f"The {name} shock must be a number (−0.2 for −20%).")
        if not np.isfinite(move) or move <= MAX_LOSS:
            raise ValueError(f"The {name} shock must be a finite move above −100%.")
    active = pd.Series({name: float(move) for name, move in shocks.items() if move != 0})
    if active.empty:
        raise ValueError("Enter at least one non-zero shock.")
    return active
