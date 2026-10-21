"""Compare a fixed-weight portfolio with the S&P 500 benchmark (SPY).

Both inputs are adjusted close prices (splits and dividends applied), as
returned by ``risklens.data.fetch_prices`` and ``fetch_benchmark_prices``.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from risklens.analytics.metrics import (
    RETURN_NOISE_TOLERANCE,
    annualized_return,
    annualized_volatility,
    cumulative_wealth,
    portfolio_returns,
)
from risklens.data import to_returns

MIN_ALIGNED_PRICES = 2
MIN_STATISTIC_RETURNS = 2  # sample covariance and volatility need two returns


@dataclass(frozen=True)
class BenchmarkStatistics:
    """Portfolio vs. benchmark on shared dates. Rates are fractions, not percents.

    Attributes:
        excess_return: annualized portfolio return minus annualized benchmark
            return (mean daily return x 252 for each).
        beta: sample covariance of daily returns / benchmark variance; 1.0
            moves with the market, 0.5 moves half as much.
        correlation: Pearson correlation of daily returns; NaN when the
            portfolio's returns are constant.
        tracking_error: annualized volatility of daily (portfolio - benchmark)
            returns, x sqrt(252).
    """

    excess_return: float
    beta: float
    correlation: float
    tracking_error: float


def _aligned_returns(
    asset_prices: pd.DataFrame,
    weights: Sequence[float],
    benchmark_prices: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.DatetimeIndex]:
    """Daily portfolio and benchmark returns on the dates both have prices.

    Returns ``(portfolio, benchmark, shared_price_dates)``. Returns are indexed
    by every shared date after the first, which is the base date.

    Raises:
        ValueError: on wrong input types, mismatched time zones, fewer than
            ``MIN_ALIGNED_PRICES`` shared dates, invalid weights, or prices
            that are not dated, finite, and positive.
    """
    if not isinstance(asset_prices, pd.DataFrame):
        raise ValueError("asset_prices must be a pandas DataFrame.")
    if not isinstance(benchmark_prices, pd.Series):
        raise ValueError("benchmark_prices must be a pandas Series.")
    asset_tz = getattr(asset_prices.index, "tz", None)
    bench_tz = getattr(benchmark_prices.index, "tz", None)
    if (asset_tz is None) != (bench_tz is None):
        raise ValueError("Asset and benchmark dates must both have, or both lack, a time zone.")

    assets = asset_prices.dropna()
    bench = benchmark_prices.dropna()
    shared = assets.index.intersection(bench.index).sort_values()
    if len(shared) < MIN_ALIGNED_PRICES:
        raise ValueError(
            f"Need at least {MIN_ALIGNED_PRICES} shared price dates with the benchmark."
        )
    port = portfolio_returns(to_returns(assets.loc[shared]), weights)
    return port, to_returns(bench.loc[shared]).rename("benchmark"), shared


def compare_to_benchmark(
    asset_prices: pd.DataFrame,
    weights: Sequence[float],
    benchmark_prices: pd.Series,
) -> pd.DataFrame:
    """Normalized growth of the portfolio and the benchmark from a common 1.0.

    ``asset_prices`` has one column per asset, ``weights`` follow its column
    order, and ``benchmark_prices`` is the SPY price series. Only dates where
    every asset and the benchmark have a price are used. The first shared
    date is the base date where both curves equal 1.0; 1.10 later means up
    10% since then. The portfolio is rebalanced daily to fixed weights.

    Returns:
        DataFrame indexed by date with columns ``portfolio`` and ``benchmark``.

    Raises:
        ValueError: if fewer than 2 dates are shared, weights are invalid,
            or prices produce impossible returns.
    """
    port, bench, shared = _aligned_returns(asset_prices, weights, benchmark_prices)
    curves = pd.DataFrame(
        {"portfolio": cumulative_wealth(port), "benchmark": cumulative_wealth(bench)}
    )
    base = pd.DataFrame({"portfolio": [1.0], "benchmark": [1.0]}, index=shared[:1])
    return pd.concat([base, curves])


def benchmark_statistics(
    asset_prices: pd.DataFrame,
    weights: Sequence[float],
    benchmark_prices: pd.Series,
) -> BenchmarkStatistics:
    """Excess return, beta, correlation, and tracking error against SPY.

    Inputs and date alignment match ``compare_to_benchmark``: adjusted prices,
    weights in column order, only dates shared by every asset and SPY.

    Raises:
        ValueError: on the same inputs as ``compare_to_benchmark``, fewer
            than ``MIN_STATISTIC_RETURNS`` shared daily returns, or constant
            benchmark returns (beta is undefined).
    """
    port, bench, _ = _aligned_returns(asset_prices, weights, benchmark_prices)
    if len(port) < MIN_STATISTIC_RETURNS:
        raise ValueError(
            f"Need at least {MIN_STATISTIC_RETURNS} shared daily returns for benchmark statistics."
        )
    # Compare std, not variance, to the noise floor: np.isclose(variance, 0)
    # rejected real low-volatility benchmarks (daily volatility under 0.01%).
    if float(np.std(bench, ddof=1)) <= RETURN_NOISE_TOLERANCE:
        raise ValueError("Benchmark returns are constant, so beta is undefined.")
    bench_variance = float(np.var(bench, ddof=1))
    return BenchmarkStatistics(
        excess_return=annualized_return(port) - annualized_return(bench),
        beta=float(np.cov(port, bench, ddof=1)[0, 1]) / bench_variance,
        correlation=float(port.corr(bench)),
        tracking_error=annualized_volatility(port - bench),
    )
