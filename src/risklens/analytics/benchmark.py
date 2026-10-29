"""Compare a fixed-weight portfolio with the S&P 500 benchmark (SPY).

Both inputs are adjusted close prices (splits and dividends applied), as
returned by ``risklens.data.fetch_prices`` and ``fetch_benchmark_prices``.
"""

from collections.abc import Sequence

import pandas as pd

from risklens.analytics.metrics import cumulative_wealth, portfolio_returns
from risklens.data import to_returns

MIN_ALIGNED_PRICES = 2


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
    assets = asset_prices.dropna()
    bench = benchmark_prices.dropna()
    shared = assets.index.intersection(bench.index).sort_values()
    if len(shared) < MIN_ALIGNED_PRICES:
        raise ValueError(
            f"Need at least {MIN_ALIGNED_PRICES} shared price dates with the benchmark."
        )
    assets, bench = assets.loc[shared], bench.loc[shared]

    port_wealth = cumulative_wealth(portfolio_returns(to_returns(assets), weights))
    bench_wealth = cumulative_wealth(to_returns(bench))
    curves = pd.DataFrame({"portfolio": port_wealth, "benchmark": bench_wealth})
    base = pd.DataFrame({"portfolio": [1.0], "benchmark": [1.0]}, index=shared[:1])
    return pd.concat([base, curves])
