"""Peak memory of one Monte Carlo run at the largest supported size.

Run from the repository root:

    python benchmarks/simulation_memory.py

The history and seed are fixed, so repeated runs simulate the same paths.
``tracemalloc`` counts NumPy array buffers, so the reported peak is the
extra memory ``simulate_portfolio`` allocates, independent of the Python
process baseline. One full ``n_paths x horizon_days`` float64 array is shown
for scale.
"""

import time
import tracemalloc

import numpy as np
import pandas as pd

from risklens.analytics.simulation import MAX_HORIZON_DAYS, MAX_PATHS, simulate_portfolio

HISTORY_DAYS = 1_260
HISTORY_SEED = 0
SIMULATION_SEED = 42
BYTES_PER_FLOAT = 8
MB = 1_000_000


def benchmark_returns() -> pd.Series:
    """Five years of synthetic daily simple returns, identical on every run."""
    rng = np.random.default_rng(HISTORY_SEED)
    dates = pd.bdate_range("2020-01-01", periods=HISTORY_DAYS)
    return pd.Series(rng.normal(0.0004, 0.01, HISTORY_DAYS), index=dates)


def measure(returns: pd.Series, horizon_days: int, n_paths: int) -> tuple[float, float]:
    """Return (peak traced MB, seconds) for one simulation."""
    tracemalloc.start()
    started = time.perf_counter()
    simulate_portfolio(returns, horizon_days=horizon_days, n_paths=n_paths, seed=SIMULATION_SEED)
    seconds = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / MB, seconds


def main() -> None:
    returns = benchmark_returns()
    measure(returns, horizon_days=1, n_paths=1_000)  # warm imports and caches first
    peak_mb, seconds = measure(returns, MAX_HORIZON_DAYS, MAX_PATHS)
    array_mb = MAX_PATHS * MAX_HORIZON_DAYS * BYTES_PER_FLOAT / MB
    print(f"paths x days:        {MAX_PATHS:,} x {MAX_HORIZON_DAYS:,}")
    print(f"one full array:      {array_mb:,.1f} MB")
    print(f"peak traced memory:  {peak_mb:,.1f} MB ({peak_mb / array_mb:.2f} full arrays)")
    print(f"wall time:           {seconds:.2f} s")


if __name__ == "__main__":
    main()
