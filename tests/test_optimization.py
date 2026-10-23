"""Deterministic unit tests for long-only mean-variance optimization."""

import numpy as np
import pandas as pd
import pytest

from risklens.analytics import (
    TRADING_DAYS_PER_YEAR,
    OptimizedPortfolio,
    analyze_portfolio,
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


# --- shared result contract ---------------------------------------------------------


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
@pytest.mark.parametrize("rate", [0.0, 0.03])
def test_weights_are_long_only_and_fully_invested(optimizer: object, rate: float) -> None:
    prices = five_assets()
    result = optimizer(prices, risk_free_rate=rate)  # type: ignore[operator]

    assert isinstance(result, OptimizedPortfolio)
    assert list(result.weights.index) == list(prices.columns)
    assert result.weights.sum() == pytest.approx(1.0, abs=1e-12)
    assert ((result.weights >= 0) & (result.weights <= 1)).all()


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
@pytest.mark.parametrize("rate", [0.0, 0.03])
def test_reported_metrics_match_analyze_portfolio(optimizer: object, rate: float) -> None:
    prices = five_assets()
    result = optimizer(prices, risk_free_rate=rate)  # type: ignore[operator]
    metrics = analyze_portfolio(prices, result.weights.to_numpy(), rate)

    assert result.expected_return == pytest.approx(metrics.annualized_return, rel=1e-12)
    assert result.volatility == pytest.approx(metrics.annualized_volatility, rel=1e-12)
    assert result.sharpe_ratio == pytest.approx(metrics.sharpe_ratio, rel=1e-12)


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_diagnostics_report_a_converged_full_rank_solve(optimizer: object) -> None:
    diagnostics = optimizer(five_assets()).diagnostics  # type: ignore[operator]

    assert diagnostics.converged
    assert diagnostics.status == 0
    assert diagnostics.iterations >= 1
    assert diagnostics.observations == 499
    assert diagnostics.covariance_rank == 5
    assert not diagnostics.singular_covariance


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_results_are_deterministic_and_inputs_unchanged(optimizer: object) -> None:
    prices = five_assets()
    before = prices.copy()

    first = optimizer(prices, risk_free_rate=0.02)  # type: ignore[operator]
    second = optimizer(prices, risk_free_rate=0.02)  # type: ignore[operator]

    pd.testing.assert_series_equal(first.weights, second.weights)
    assert (first.expected_return, first.volatility, first.sharpe_ratio) == (
        second.expected_return, second.volatility, second.sharpe_ratio
    )
    assert first.diagnostics == second.diagnostics
    pd.testing.assert_frame_equal(prices, before)


@pytest.mark.parametrize("optimizer", OPTIMIZERS)
def test_single_asset_gets_all_the_weight(optimizer: object) -> None:
    result = optimizer(make_prices([5e-4], [0.01]))  # type: ignore[operator]

    assert result.weights.tolist() == [1.0]


# --- minimum volatility ---------------------------------------------------------------


def test_min_volatility_matches_two_asset_closed_form() -> None:
    prices = make_prices([3e-4, 5e-4], [0.01, 0.02], seed=1)
    _, covariance, _ = estimate_inputs(prices)
    s = covariance.to_numpy()
    first = (s[1, 1] - s[0, 1]) / (s[0, 0] + s[1, 1] - 2 * s[0, 1])

    result = min_volatility_portfolio(prices)

    np.testing.assert_allclose(result.weights, [first, 1 - first], atol=1e-8)


@pytest.mark.parametrize("seed", range(3))
def test_min_volatility_is_not_beaten_by_any_sampled_portfolio(seed: int) -> None:
    prices = five_assets(seed)
    _, covariance, _ = estimate_inputs(prices)
    weights = random_portfolios(5)
    vols = np.sqrt(np.einsum("ij,jk,ik->i", weights, covariance.to_numpy(), weights))

    assert min_volatility_portfolio(prices).volatility <= vols.min() * (1 + 1e-9)


def test_min_volatility_weights_ignore_risk_free_rate() -> None:
    prices = five_assets()
    low = min_volatility_portfolio(prices, risk_free_rate=0.0)
    high = min_volatility_portfolio(prices, risk_free_rate=0.05)

    pd.testing.assert_series_equal(low.weights, high.weights)
    assert high.sharpe_ratio == pytest.approx((high.expected_return - 0.05) / high.volatility)
