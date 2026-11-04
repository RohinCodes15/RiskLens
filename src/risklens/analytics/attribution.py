"""Where portfolio risk comes from: factor exposures and sector/country breakdowns."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from risklens.analytics.metrics import (
    BPS_PER_UNIT,
    MIN_VOLATILITY_OBS,
    TRADING_DAYS_PER_YEAR,
    _portfolio_inputs,
    _turnover,
    risk_contributions,
)
from risklens.validation import validate_cost_bps, validate_weights

FACTOR_COLUMNS = ("Mkt-RF", "SMB", "HML", "Mom")  # Fama-French 3 factors + Carhart momentum
RISK_FREE_COLUMN = "RF"
MIN_FACTOR_OBS = 60  # about three months of shared trading days
COST_LABEL = "Trading costs"  # risk-share row for the cost drag; tickers never contain spaces


@dataclass(frozen=True)
class FactorExposure:
    """Result of regressing portfolio excess returns on the factor returns.

    ``alpha`` is annualized (daily intercept × 252, a fraction). ``betas`` are
    unitless loadings indexed by ``FACTOR_COLUMNS``. ``r_squared`` is the share
    of daily excess-return variance the factors explain (0–1).
    """

    alpha: float
    betas: pd.Series
    r_squared: float
    observations: int
    first_date: pd.Timestamp
    last_date: pd.Timestamp


def factor_exposure(returns: pd.Series, factors: pd.DataFrame) -> FactorExposure:
    """Regress daily portfolio excess returns on Fama-French-Carhart factors by OLS.

    ``returns`` are simple daily portfolio returns (fractions) on a date index.
    ``factors`` holds daily factor returns as fractions with the columns in
    ``FACTOR_COLUMNS`` plus ``RF``. Only dates in both are used.

    Raises:
        ValueError: if a factor column is missing, values are not finite, fewer
            than ``MIN_FACTOR_OBS`` dates overlap, or the excess returns are constant.
    """
    missing = [c for c in (*FACTOR_COLUMNS, RISK_FREE_COLUMN) if c not in factors.columns]
    if missing:
        raise ValueError(f"Factor data is missing columns: {', '.join(missing)}.")
    data = pd.concat([returns.rename("portfolio"), factors], axis=1, join="inner")
    if len(data) < MIN_FACTOR_OBS:
        raise ValueError(
            f"Need at least {MIN_FACTOR_OBS} days shared with the factor data; got {len(data)}."
        )
    values = data.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Returns and factor data must be finite.")
    excess = data["portfolio"].to_numpy(dtype=float) - data[RISK_FREE_COLUMN].to_numpy(dtype=float)
    total = float(np.sum((excess - excess.mean()) ** 2))
    if total == 0:
        raise ValueError("Portfolio excess returns are constant; the regression is undefined.")
    design = np.column_stack([np.ones(len(data)), data[list(FACTOR_COLUMNS)].to_numpy(float)])
    coef, *_ = np.linalg.lstsq(design, excess, rcond=None)
    residual = float(np.sum((excess - design @ coef) ** 2))
    return FactorExposure(
        alpha=float(coef[0]) * TRADING_DAYS_PER_YEAR,
        betas=pd.Series(coef[1:], index=list(FACTOR_COLUMNS), name="beta"),
        r_squared=1.0 - residual / total,
        observations=len(data),
        first_date=data.index[0],
        last_date=data.index[-1],
    )


def _held_weights(values: np.ndarray, w: np.ndarray, periods: np.ndarray) -> np.ndarray:
    """Weights held at the start of each return row: ``w`` on a reset row, then drifted.

    Row t of the result times row t of ``values`` sums to that day's gross
    portfolio return, the same number ``portfolio_returns`` gives before costs.
    A period that lost everything holds nothing (all zeros).
    """
    held = np.empty_like(values)
    starts = np.flatnonzero(np.diff(periods, prepend=-1))
    for start, stop in zip(starts, [*starts[1:], len(values)], strict=True):
        growth = np.cumprod(1.0 + values[start : stop - 1], axis=0)  # through each earlier day
        holdings = np.vstack([w, w * growth])
        totals = holdings.sum(axis=1, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            held[start:stop] = np.where(totals > 0, holdings / totals, 0.0)
    return held


def rebalanced_risk_contributions(
    returns: pd.DataFrame,
    weights: Sequence[float],
    rebalance: str = "daily",
    cost_bps: float = 0.0,
) -> pd.Series:
    """Each holding's share of the variance of the portfolio you actually hold.

    The net daily portfolio return (``portfolio_returns`` with ``rebalance``
    and ``cost_bps``) splits exactly into one piece per holding, the weight
    it held that morning times its return, plus a trading-cost piece,
    −cost × (1 + gross return). A piece's share is its sample covariance with
    the portfolio return divided by the portfolio's variance, so the shares
    sum to 1. With daily rebalancing and no costs this equals
    ``risk_contributions``. The ``COST_LABEL`` row is added only when
    ``cost_bps`` > 0; it is usually tiny and can be negative.

    Raises:
        ValueError: on the inputs ``portfolio_returns`` rejects, fewer than 2
            returns, or zero portfolio variance.
    """
    cost_rate = validate_cost_bps(cost_bps) / BPS_PER_UNIT
    values, w, periods = _portfolio_inputs(returns, weights, rebalance)
    if len(values) < MIN_VOLATILITY_OBS:
        raise ValueError("need at least 2 rows of returns to estimate covariance")
    pieces = _held_weights(values, w, periods) * values
    gross = pieces.sum(axis=1)
    cost = -cost_rate * 2.0 * _turnover(values, w, periods) * (1.0 + gross)
    net = gross + cost
    centered = net - net.mean()
    variance = float(centered @ centered)
    if variance <= 0:
        raise ValueError("portfolio variance is zero; risk shares are undefined")
    parts = np.column_stack([pieces, cost]) if cost_rate > 0 else pieces
    shares = (parts - parts.mean(axis=0)).T @ centered / variance
    index = [*returns.columns, COST_LABEL] if cost_rate > 0 else list(returns.columns)
    return pd.Series(shares, index=index, name="risk_contribution")


def group_breakdown(
    returns: pd.DataFrame, weights: Sequence[float], groups: pd.Series
) -> pd.DataFrame:
    """Sum allocation weights and risk shares by a label such as sector or country.

    ``returns`` holds simple daily asset returns, one column per ticker;
    ``groups`` maps each ticker to its label. Returns a DataFrame indexed by
    label with ``weight`` and ``risk_share`` columns (fractions, each summing
    to 1), sorted by risk share, largest first.

    Raises:
        ValueError: if a ticker has no label, or ``risk_contributions`` rejects
            the inputs.
    """
    w = validate_weights(weights, returns.shape[1])
    missing = [t for t in returns.columns if t not in groups.index]
    if missing:
        raise ValueError(f"No label for: {', '.join(missing)}.")
    labels = groups.reindex(returns.columns).to_numpy()
    table = pd.DataFrame(
        {"weight": w, "risk_share": risk_contributions(returns, w).to_numpy()},
        index=pd.Index(labels, name=groups.name),
    )
    return table.groupby(level=0, sort=False).sum().sort_values("risk_share", ascending=False)
