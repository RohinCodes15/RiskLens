"""Where portfolio risk comes from: factor exposures and sector/country breakdowns."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from risklens.analytics.metrics import TRADING_DAYS_PER_YEAR

FACTOR_COLUMNS = ("Mkt-RF", "SMB", "HML", "Mom")  # Fama-French 3 factors + Carhart momentum
RISK_FREE_COLUMN = "RF"
MIN_FACTOR_OBS = 60  # about three months of shared trading days


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
