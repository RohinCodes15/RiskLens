"""Monte Carlo simulation of future portfolio wealth from historical returns.

Model (geometric Brownian motion, i.i.d. daily log returns):
    1. Convert historical simple daily portfolio returns r to log returns
       log(1 + r).
    2. Estimate the daily mean (mu) and sample volatility (sigma, ddof=1)
       of those log returns.
    3. Draw each future day's log return from Normal(mu, sigma), add them up
       along each path, and convert back with exp(). Every path starts at
       wealth 1.0, so 1.25 means up 25% and wealth can never go negative.

Assumptions and limitations, so read results as scenarios, not forecasts:
    - Returns are independent and identically distributed, so volatility
      clustering, regime changes, and momentum are ignored.
    - Normal log returns understate fat tails, so crashes beyond the
      historical sample can be worse than the 5th percentile suggests.
    - mu and sigma are estimated from a finite sample and treated as known,
      so short histories give unreliable results.
    - The portfolio keeps fixed weights; no fees, taxes, or cash flows.
    - Future dates are weekdays after the last historical date; exchange
      holidays are not removed.
    - Percentile paths are computed day by day across all paths. The median
      path is not one simulated path.

No look-ahead: parameters come only from the returns passed in, and every
simulated date is strictly after the last of them. Pass only history up to
the date you want the simulation to start.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from risklens.analytics.metrics import (
    MIN_VOLATILITY_OBS,
    RETURN_NOISE_TOLERANCE,
    _validate_returns,
)

MIN_PATHS = 1_000
MAX_PATHS = 10_000
MIN_HORIZON_DAYS = 1
MAX_HORIZON_DAYS = 1_260  # five years of trading days; bounds memory use
DEFAULT_SEED = 42
PERCENTILES = (5, 25, 50, 75, 95)
PERCENTILE_LABELS = ("p5", "p25", "median", "p75", "p95")


@dataclass(frozen=True)
class MonteCarloResult:
    """Simulated wealth scenarios. Rates are fractions, not percents.

    Attributes:
        percentile_paths: wealth percentiles by date, columns ``p5``, ``p25``,
            ``median``, ``p75``, ``p95``. The first row is the last
            historical date, where every column is 1.0.
        terminal_returns: one cumulative return per path at the horizon
            (ending wealth - 1.0), shape ``(n_paths,)``.
        loss_probability: share of paths ending below their starting wealth.
        daily_mean: estimated mean daily log return (mu).
        daily_volatility: estimated daily log-return volatility (sigma);
            0.0 when historical returns are constant.
    """

    percentile_paths: pd.DataFrame
    terminal_returns: np.ndarray
    loss_probability: float
    daily_mean: float
    daily_volatility: float


def _validate_int(value: object, name: str, low: int, high: int) -> int:
    """Return ``value`` as int if it is a whole number in ``[low, high]``."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be a whole number.")
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low:,} and {high:,}; got {value:,}.")
    return int(value)


def _estimate_parameters(returns: pd.Series) -> tuple[float, float]:
    """Daily mean and sample volatility of log returns from simple returns.

    Raises:
        ValueError: if returns are not a dated, sorted, finite Series of at
            least 2 values, or include a -100% day.
    """
    values = _validate_returns(returns, MIN_VOLATILITY_OBS)
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise ValueError("returns must be indexed by date.")
    if not returns.index.is_monotonic_increasing or not returns.index.is_unique:
        raise ValueError("Return dates must be sorted and unique.")
    if np.any(values <= -1):
        raise ValueError("A -100% daily return leaves no wealth to simulate.")
    log_returns = np.log1p(values)
    sigma = float(log_returns.std(ddof=1))
    if sigma <= RETURN_NOISE_TOLERANCE:
        sigma = 0.0  # constant history up to float rounding: one deterministic curve
    return float(log_returns.mean()), sigma


def _future_dates(last_date: pd.Timestamp, horizon_days: int) -> pd.DatetimeIndex:
    """The start date plus ``horizon_days`` weekdays strictly after it.

    Future dates keep the start date's time of day, so the index is evenly
    spaced even when prices are stamped at the close (e.g. 16:00).
    """
    future = pd.bdate_range(
        last_date + pd.offsets.BDay(1), periods=horizon_days, tz=last_date.tz, normalize=False
    )
    return pd.DatetimeIndex([last_date]).append(future)


def simulate_portfolio(
    daily_returns: pd.Series,
    horizon_days: int = 252,
    n_paths: int = MIN_PATHS,
    seed: int = DEFAULT_SEED,
) -> MonteCarloResult:
    """Simulate future wealth paths from historical daily portfolio returns.

    ``daily_returns`` are simple daily returns as fractions (for example
    ``PortfolioMetrics.daily_returns``). The same inputs and ``seed`` always
    give the same result. See the module docstring for assumptions.

    Args:
        daily_returns: dated historical returns; only these are used.
        horizon_days: trading days to simulate, 1 to 1,260.
        n_paths: number of simulated paths, 1,000 to 10,000.
        seed: non-negative integer seed for NumPy's random generator.

    Raises:
        ValueError: on invalid returns, horizon, path count, or seed.
    """
    mu, sigma = _estimate_parameters(daily_returns)
    horizon_days = _validate_int(horizon_days, "horizon_days", MIN_HORIZON_DAYS, MAX_HORIZON_DAYS)
    n_paths = _validate_int(n_paths, "n_paths", MIN_PATHS, MAX_PATHS)
    seed = _validate_int(seed, "seed", 0, 2**32 - 1)
    dates = _future_dates(daily_returns.index[-1], horizon_days)
    rng = np.random.default_rng(seed)
    daily_log_returns = rng.normal(mu, sigma, size=(n_paths, horizon_days))
    growth = np.exp(np.cumsum(daily_log_returns, axis=1))
    wealth = np.hstack([np.ones((n_paths, 1)), growth])
    bands = np.percentile(wealth, PERCENTILES, axis=0)
    terminal_returns = wealth[:, -1] - 1.0
    return MonteCarloResult(
        percentile_paths=pd.DataFrame(bands.T, index=dates, columns=PERCENTILE_LABELS),
        terminal_returns=terminal_returns,
        loss_probability=float(np.mean(terminal_returns < 0.0)),
        daily_mean=mu,
        daily_volatility=sigma,
    )
 