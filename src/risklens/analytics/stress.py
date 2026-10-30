"""Historical stress tests: replay documented market windows on actual prices.

Method:
    1. Keep only dates inside the scenario window where every asset has an
       actual adjusted close. Prices are never forward-filled, backfilled, or
       interpolated, so a day one asset did not trade is dropped for all.
    2. Turn those prices into simple daily returns and combine them with the
       given fixed weights (daily rebalanced) via ``portfolio_returns``.
    3. Report cumulative return, max drawdown, and annualized volatility with
       the existing metric functions.

A scenario is marked unavailable, with a reason, when any asset's price
history does not cover the whole window or too few common prices remain.

Limitation: this applies today's weights to past returns. It is not the
portfolio's actual historical holdings, trades, fees, or taxes.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from risklens.analytics.metrics import (
    MIN_VOLATILITY_OBS,
    annualized_volatility,
    cumulative_wealth,
    max_drawdown,
    portfolio_returns,
)
from risklens.data import to_returns
from risklens.validation import validate_weights

MIN_WINDOW_PRICES = MIN_VOLATILITY_OBS + 1  # three prices give two returns
# A window edge may fall on a weekend or an exchange holiday. Weekends are
# never counted; allow at most this many weekdays (one holiday) between the
# edge and an asset's first or last actual price.
MAX_EDGE_WEEKDAYS = 1
HYPOTHETICAL_NOTE = (
    "Hypothetical: current fixed weights applied to past returns, "
    "not the portfolio's actual historical holdings."
)


@dataclass(frozen=True)
class StressScenario:
    """A named historical window; ``start`` and ``end`` are inclusive dates."""

    name: str
    start: pd.Timestamp
    end: pd.Timestamp
    description: str = ""


@dataclass(frozen=True)
class StressResult:
    """Realized portfolio outcome over one scenario. Rates are fractions.

    Attributes:
        scenario: the window that was tested.
        available: False when the data cannot cover the window honestly.
        reason: why the scenario is unavailable; None when available.
        cumulative_return: ending wealth / starting wealth - 1 over the
            window (-0.30 means a 30% loss); None when unavailable.
        max_drawdown: worst peak-to-trough decline inside the window, as a
            negative fraction; None when unavailable.
        annualized_volatility: daily return std (ddof=1) x sqrt(252);
            None when unavailable.
        first_date / last_date: first and last actual price dates used.
        n_returns: number of daily returns in the window.
        note: reminder that results are hypothetical.
    """

    scenario: StressScenario
    available: bool
    reason: str | None = None
    cumulative_return: float | None = None
    max_drawdown: float | None = None
    annualized_volatility: float | None = None
    first_date: pd.Timestamp | None = None
    last_date: pd.Timestamp | None = None
    n_returns: int = 0
    note: str = HYPOTHETICAL_NOTE


def _parse_date(value: str | date | pd.Timestamp, label: str) -> pd.Timestamp:
    """Return ``value`` as a timezone-naive midnight timestamp."""
    try:
        stamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} date is not a valid date: {value!r}.") from exc
    if pd.isna(stamp):
        raise ValueError(f"{label} date is missing.")
    return (stamp.tz_localize(None) if stamp.tz else stamp).normalize()


def custom_scenario(
    start: str | date | pd.Timestamp,
    end: str | date | pd.Timestamp,
    name: str = "Custom range",
) -> StressScenario:
    """Build a user-defined scenario from inclusive ``start`` and ``end`` dates.

    Raises:
        ValueError: if a date does not parse, start is not before end, or
            the name is blank.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Scenario name must not be blank.")
    start_ts, end_ts = _parse_date(start, "Start"), _parse_date(end, "End")
    if start_ts >= end_ts:
        raise ValueError("Start date must be before end date.")
    return StressScenario(name.strip(), start_ts, end_ts)


# Peak-to-trough windows of the S&P 500 (closing levels).
HISTORICAL_SCENARIOS: tuple[StressScenario, ...] = (
    StressScenario(
        "2008 financial crisis",
        pd.Timestamp("2007-10-09"),
        pd.Timestamp("2009-03-09"),
        "S&P 500 peak on 2007-10-09 to the trough on 2009-03-09.",
    ),
    StressScenario(
        "2020 COVID crash",
        pd.Timestamp("2020-02-19"),
        pd.Timestamp("2020-03-23"),
        "S&P 500 peak on 2020-02-19 to the trough on 2020-03-23.",
    ),
    StressScenario(
        "2022 bear market",
        pd.Timestamp("2022-01-03"),
        pd.Timestamp("2022-10-12"),
        "S&P 500 peak on 2022-01-03 to the trough on 2022-10-12.",
    ),
)


def _validate_price_history(prices: pd.DataFrame) -> pd.DataFrame:
    """Return a float copy of dated prices; NaN means "no observation".

    Raises:
        ValueError: if prices are not a DataFrame with unique columns and a
            sorted, unique DatetimeIndex, or an observed price is
            non-numeric, infinite, or not positive.
    """
    if not isinstance(prices, pd.DataFrame) or prices.shape[1] == 0:
        raise ValueError("Prices must be a pandas DataFrame with at least one asset column.")
    if not prices.columns.is_unique:
        raise ValueError("Price columns must be unique.")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Prices must be indexed by date.")
    if not (prices.index.is_monotonic_increasing and prices.index.is_unique):
        raise ValueError("Price dates must be sorted and unique.")
    if any(pd.api.types.is_bool_dtype(t) for t in prices.dtypes):
        raise ValueError("Prices must be numbers.")
    try:
        clean = prices.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Prices must be numbers.") from exc
    observed = clean.to_numpy()[~clean.isna().to_numpy()]
    if not np.all(np.isfinite(observed)) or np.any(observed <= 0):
        raise ValueError("Prices must be finite and positive where present.")
    return clean


def _naive_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Calendar dates of ``index`` without timezone, for comparing to windows."""
    return (index.tz_localize(None) if index.tz else index).normalize()


ONE_DAY = pd.Timedelta(days=1)


def _weekdays_between(first: pd.Timestamp, last: pd.Timestamp) -> int:
    """Number of Monday-Friday dates in ``[first, last)``; 0 if last <= first."""
    if last <= first:
        return 0
    return int(np.busday_count(first.date(), last.date()))


def _coverage_gaps(prices: pd.DataFrame, scenario: StressScenario) -> list[str]:
    """Describe each asset whose actual history does not span the window."""
    dates = _naive_dates(prices.index)
    gaps = []
    for asset in prices.columns:
        observed = dates[prices[asset].notna().to_numpy()]
        if observed.empty:
            gaps.append(f"{asset} has no price data")
        elif _weekdays_between(scenario.start, observed[0]) > MAX_EDGE_WEEKDAYS:
            gaps.append(f"{asset} history starts {observed[0].date()}")
        elif _weekdays_between(observed[-1] + ONE_DAY, scenario.end + ONE_DAY) > MAX_EDGE_WEEKDAYS:
            gaps.append(f"{asset} history ends {observed[-1].date()}")
    return gaps


def _window(prices: pd.DataFrame, scenario: StressScenario) -> pd.DataFrame:
    """Rows inside the window where every asset has an actual price."""
    dates = _naive_dates(prices.index)
    inside = (dates >= scenario.start) & (dates <= scenario.end)
    return prices.loc[inside].dropna(how="any")


def stress_test(
    prices: pd.DataFrame, weights: Sequence[float], scenario: StressScenario
) -> StressResult:
    """Realized fixed-weight portfolio results over one historical window.

    ``prices`` are adjusted closes, one column per asset in ``weights`` order;
    NaN marks dates an asset has no observation (for example before listing).

    Raises:
        ValueError: on invalid prices or weights. Missing history is not an
            error: it returns ``available=False`` with a reason.
    """
    clean = _validate_price_history(prices)
    w = validate_weights(weights, clean.shape[1])
    gaps = _coverage_gaps(clean, scenario)
    if gaps:
        return StressResult(scenario, False, "Insufficient history: " + "; ".join(gaps) + ".")
    window = _window(clean, scenario)
    if len(window) < MIN_WINDOW_PRICES:
        reason = f"Need {MIN_WINDOW_PRICES} common price dates in the window; got {len(window)}."
        return StressResult(scenario, False, reason)
    daily = portfolio_returns(to_returns(window), w)
    return StressResult(
        scenario=scenario,
        available=True,
        cumulative_return=float(cumulative_wealth(daily).iloc[-1] - 1.0),
        max_drawdown=max_drawdown(daily),
        annualized_volatility=annualized_volatility(daily),
        first_date=window.index[0],
        last_date=window.index[-1],
        n_returns=len(daily),
    )


def run_stress_tests(
    prices: pd.DataFrame,
    weights: Sequence[float],
    scenarios: Sequence[StressScenario] = HISTORICAL_SCENARIOS,
) -> list[StressResult]:
    """Run ``stress_test`` for each scenario, keeping the scenario order."""
    return [stress_test(prices, weights, scenario) for scenario in scenarios]
