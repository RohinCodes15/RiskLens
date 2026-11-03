"""What-if trades: move part of the portfolio between tickers and compare metrics.

A trade sells ``amount`` of total portfolio value from one ticker and buys the
same value of another, which may be a ticker not yet held. Both weight sets
are then replayed on the same past adjusted prices with the same rebalancing
and trading costs, so the only difference between the two is the trade.

Limitation: like every RiskLens metric, this applies fixed target weights to
past returns. It is not a forecast of how the trade will perform.
"""

import numbers

import numpy as np
import pandas as pd

from risklens.analytics.engine import analyze_portfolio
from risklens.analytics.metrics import (
    BPS_PER_UNIT,
    DEFAULT_VAR_CONFIDENCE,
    historical_cvar,
    historical_var,
)
from risklens.validation import validate_cost_bps, validate_weights

# Lets "sell the whole position" match a weight that carries float rounding.
TRADE_TOLERANCE = 1e-9
COMPARISON_METRICS = (
    "annualized_return",
    "annualized_volatility",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "var",
    "cvar",
    "annual_turnover",
)


def _checked_weights(weights: pd.Series) -> pd.Series:
    """Return ``weights`` as a float Series after the usual weight checks."""
    if not isinstance(weights, pd.Series):
        raise ValueError("Weights must be a pandas Series indexed by ticker.")
    if not weights.index.is_unique:
        raise ValueError("Each ticker may appear only once in the weights.")
    return pd.Series(validate_weights(weights.to_numpy(), len(weights)), index=weights.index)


def _checked_amount(amount: float) -> float:
    """Return ``amount`` as a float, or raise unless it is a finite positive number."""
    if isinstance(amount, (bool, np.bool_)) or not isinstance(amount, numbers.Real):
        raise ValueError("Trade amount must be a number (0.10 for 10% of the portfolio).")
    value = float(amount)
    if not np.isfinite(value) or value <= 0:
        raise ValueError("Trade amount must be greater than 0.")
    return value


def trade_weights(weights: pd.Series, sell: str, buy: str, amount: float) -> pd.Series:
    """Weights after moving ``amount`` of the portfolio from ``sell`` to ``buy``.

    ``weights`` are fractions indexed by ticker that sum to 1. ``amount`` is a
    fraction of the whole portfolio (0.10 moves 10% of total value), not of
    the ``sell`` position. ``buy`` may be a ticker not yet held; it is added
    at the end. A ticker sold down to zero keeps a 0 weight so before and
    after line up. The input is not modified.

    Raises:
        ValueError: if the weights are invalid, ``sell`` is not held, ``buy``
            is blank or equals ``sell``, or ``amount`` is not in
            (0, weight of ``sell``].
    """
    before = _checked_weights(weights)
    value = _checked_amount(amount)
    if sell not in before.index:
        raise ValueError(f"{sell} is not in the portfolio, so it cannot be sold.")
    if not isinstance(buy, str) or not buy.strip():
        raise ValueError("Enter a ticker to buy.")
    if buy == sell:
        raise ValueError("Choose a different ticker to buy than the one you sell.")
    held = float(before[sell])
    if value > held + TRADE_TOLERANCE:
        raise ValueError(
            f"Cannot sell {value:.2%} of the portfolio from {sell}; it is only {held:.2%}."
        )
    moved = min(value, held)
    index = before.index if buy in before.index else before.index.append(pd.Index([buy]))
    after = before.reindex(index, fill_value=0.0)
    change = pd.Series({sell: -moved, buy: moved}).reindex(index, fill_value=0.0)
    return (after + change).rename("weight")


def trade_cost(amount: float, cost_bps: float) -> float:
    """One-time cost of a trade as a fraction of portfolio value.

    Selling ``amount`` and buying the same value trades ``2 × amount`` dollars
    per dollar of portfolio, each charged ``cost_bps`` basis points, the same
    rule ``portfolio_returns`` uses on rebalance dates.

    Raises:
        ValueError: if ``amount`` is not a positive number or ``cost_bps`` is
            invalid (see ``validate_cost_bps``).
    """
    return 2.0 * _checked_amount(amount) * validate_cost_bps(cost_bps) / BPS_PER_UNIT


def _aligned(weights: pd.Series, columns: pd.Index, label: str) -> np.ndarray:
    """Weights in ``columns`` order, 0 for unlisted tickers; raise if a held ticker has no prices."""
    if not isinstance(weights, pd.Series):
        raise ValueError(f"{label} weights must be a pandas Series indexed by ticker.")
    extra = weights[~weights.index.isin(columns)]
    if (extra != 0).any():
        missing = ", ".join(map(str, extra[extra != 0].index))
        raise ValueError(f"No prices for {missing} in the {label} portfolio.")
    return weights.reindex(columns, fill_value=0.0).to_numpy(dtype=float)


def compare_portfolios(
    prices: pd.DataFrame,
    before: pd.Series,
    after: pd.Series,
    risk_free_rate: float = 0.0,
    rebalance: str = "daily",
    cost_bps: float = 0.0,
    confidence: float = DEFAULT_VAR_CONFIDENCE,
) -> pd.DataFrame:
    """Run the same metrics for two weight sets on the same adjusted prices.

    ``before`` and ``after`` are weights indexed by ticker. A ticker missing
    from one of them counts as weight 0; every ticker with a non-zero weight
    must be a column of ``prices``. Returns a DataFrame indexed by
    ``COMPARISON_METRICS`` with ``before``, ``after``, and ``change``
    (after − before) columns. ``var`` and ``cvar`` are one-day historical
    losses at ``confidence`` as positive fractions; the other rows follow
    ``PortfolioMetrics`` (annualized fractions, ratios, negative drawdown).

    Raises:
        ValueError: if a weighted ticker has no prices, or
            ``analyze_portfolio`` or the VaR functions reject the inputs.
    """
    if not isinstance(prices, pd.DataFrame):
        raise ValueError("prices must be a pandas DataFrame.")
    columns = {}
    for label, weights in (("before", before), ("after", after)):
        w = _aligned(weights, prices.columns, label)
        result = analyze_portfolio(prices, w, risk_free_rate, rebalance, cost_bps)
        daily = result.daily_returns
        columns[label] = [
            *(getattr(result, name) for name in COMPARISON_METRICS[:5]),
            historical_var(daily, confidence),
            historical_cvar(daily, confidence),
            result.annual_turnover,
        ]
    table = pd.DataFrame(columns, index=pd.Index(COMPARISON_METRICS, name="metric"))
    return table.assign(change=table["after"] - table["before"])
