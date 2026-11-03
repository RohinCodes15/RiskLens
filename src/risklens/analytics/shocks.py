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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from risklens.validation import validate_weights

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


def _shared_returns(
    asset_returns: pd.DataFrame, proxy_returns: pd.DataFrame, proxies: list[str]
) -> pd.DataFrame:
    """Asset and proxy returns on their shared dates, as one two-level frame."""
    data = pd.concat(
        {"asset": asset_returns, "proxy": proxy_returns[proxies]}, axis=1, join="inner"
    )
    if len(data) < MIN_SHOCK_OBS:
        raise ValueError(
            f"Need at least {MIN_SHOCK_OBS} days shared with the proxy data; got {len(data)}."
        )
    if not np.isfinite(data.to_numpy(dtype=float)).all():
        raise ValueError("Holding and proxy returns must be finite.")
    return data


def _regress(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS of each column of ``y`` on ``x`` plus an intercept: (betas, R² per column)."""
    design = np.column_stack([np.ones(len(x)), x])
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError(
            "The shocked proxies have no variation or move in lockstep, so their "
            "effects cannot be separated. Shock fewer of them."
        )
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    residual = ((y - design @ coef) ** 2).sum(axis=0)
    total = ((y - y.mean(axis=0)) ** 2).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r_squared = np.where(total > 0, 1.0 - residual / total, np.nan)
    return coef[1:].T, r_squared


def shock_impact(
    asset_returns: pd.DataFrame,
    proxy_returns: pd.DataFrame,
    weights: Sequence[float],
    shocks: Mapping[str, float],
) -> ShockImpact:
    """Estimate the portfolio move when the named proxies move by ``shocks``.

    ``asset_returns`` holds simple daily returns, one column per holding, in
    the order of ``weights`` (fractions summing to 1). ``proxy_returns``
    holds simple daily proxy returns with one column per proxy name.
    ``shocks`` maps proxy names to moves as fractions (−0.2 for −20%);
    zero shocks are ignored. Only dates in both tables are used.

    Raises:
        ValueError: if the weights are invalid, a shock names a missing
            proxy, is not a number above −100%, or none is non-zero, fewer
            than ``MIN_SHOCK_OBS`` dates are shared, values are not finite,
            or the shocked proxies cannot be told apart.
    """
    if not isinstance(asset_returns, pd.DataFrame) or not isinstance(proxy_returns, pd.DataFrame):
        raise ValueError("Holding and proxy returns must be pandas DataFrames.")
    w = validate_weights(weights, asset_returns.shape[1])
    active = _active_shocks(shocks, proxy_returns.columns)
    data = _shared_returns(asset_returns, proxy_returns, list(active.index))
    betas, r_squared = _regress(
        data["asset"].to_numpy(dtype=float), data["proxy"].to_numpy(dtype=float)
    )
    impact = np.maximum(betas @ active.to_numpy(), MAX_LOSS)
    holdings = pd.DataFrame(
        {"weight": w, "impact": impact, "contribution": w * impact, "r_squared": r_squared},
        index=asset_returns.columns,
    )
    return ShockImpact(
        portfolio_impact=float(holdings["contribution"].sum()),
        holdings=holdings,
        betas=pd.DataFrame(betas, index=asset_returns.columns, columns=active.index),
        shocks=active,
        observations=len(data),
        first_date=data.index[0],
        last_date=data.index[-1],
    )
