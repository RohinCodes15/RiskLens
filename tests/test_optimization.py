"""Deterministic unit tests for long-only mean-variance optimization."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    TRADING_DAYS_PER_YEAR,
    estimate_inputs,
    max_sharpe_portfolio,
    min_volatility_portfolio,
)
from risklens.data import to_returns

OPTIMIZERS = [min_volatility_portfolio, max_sharpe_portfolio]


def make_prices(
    means: list[float],
    vols: list[float],
    n: int = 500,
    seed: int = 0,
    corr: np.ndarray | None = None,
) -> pd.DataFrame:
    """Seeded adjusted prices from normal daily returns, one column per asset."""
    rng = np.random.default_rng(seed)
    shocks = rng.standard_normal((n, len(means)))
    if corr is not None:
        shocks = shocks @ np.linalg.cholesky(corr).T
    returns = np.array(means) + shocks * np.array(vols)
    return pd.DataFrame(
        100 * np.cumprod(1 + returns, axis=0),
        index=pd.bdate_range("2022-01-03", periods=n),
        columns=[f"A{i}" for i in range(len(means))],
    )


def five_assets(seed: int = 0) -> pd.DataFrame:
    return make_prices(
        [3e-4, 5e-4, 2e-4, 7e-4, 4e-4], [0.010, 0.015, 0.008, 0.025, 0.012], seed=seed
    )


def random_portfolios(n_assets: int, count: int = 20_000) -> np.ndarray:
    """Seeded long-only weights summing to 1, plus each single-asset portfolio."""
    weights = np.random.default_rng(1).dirichlet(np.ones(n_assets), count)
    return np.vstack([weights, np.eye(n_assets)])


# --- input estimation --------------------------------------------------------------


def test_estimate_inputs_annualizes_mean_and_sample_covariance() -> None:
    prices = five_assets()
    expected, covariance, n_obs = estimate_inputs(prices)
    returns = to_returns(prices)

    assert n_obs == len(prices) - 1
    pd.testing.assert_series_equal(
        expected, returns.mean() * TRADING_DAYS_PER_YEAR, check_names=False
    )
    pd.testing.assert_frame_equal(covariance, returns.cov(ddof=1) * TRADING_DAYS_PER_YEAR)


def test_estimate_inputs_needs_more_returns_than_assets() -> None:
    prices = five_assets().iloc[:6]  # 5 returns for 5 assets: covariance always singular

    with pytest.raises(ValueError, match="at least 6 daily returns to optimize 5 asset"):
        estimate_inputs(prices)
    assert estimate_inputs(five_assets().iloc[:7])[2] == 6


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_too_few_prices_are_rejected(optimizer: object) -> None:
    with pytest.raises(ValueError, match="at least 2 daily returns"):
        optimizer(make_prices([5e-4], [0.01], n=2))  # type: ignore[operator]


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_invalid_prices_are_rejected(optimizer: object) -> None:
    prices = five_assets()
    missing = prices.copy()
    missing.iloc[10, 2] = np.nan
    negative = prices.copy()
    negative.iloc[10, 2] = -1.0

    with pytest.raises(ValueError, match="missing or infinite"):
        optimizer(missing)  # type: ignore[operator]
    with pytest.raises(ValueError, match="positive"):
        optimizer(negative)  # type: ignore[operator]
    with pytest.raises(ValueError, match="indexed by date"):
        optimizer(prices.reset_index(drop=True))  # type: ignore[operator]


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
@pytest.mark.parametrize("rate", ["4%", 4.0, float("nan"), True])
def test_invalid_risk_free_rate_is_rejected(optimizer: object, rate: object) -> None:
    with pytest.raises(ValueError, match="Risk-free rate"):
        optimizer(five_assets(), risk_free_rate=rate)  # type: ignore[operator]
