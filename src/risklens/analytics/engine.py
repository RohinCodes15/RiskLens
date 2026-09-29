"""Portfolio risk engine: adjusted prices + weights -> summary metrics.

Expects adjusted close prices (splits and dividends applied), as returned by
``risklens.data.fetch_prices``, so returns reflect total return.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from risklens.analytics.metrics import (
    TRADING_DAYS_PER_YEAR,
    annualized_return,
    annualized_volatility,
    max_drawdown,
    portfolio_returns,
    rebalance_turnover,
    sharpe_ratio,
)
from risklens.data import to_returns
from risklens.validation import validate_prices, validate_risk_free_rate

MIN_PRICE_ROWS = 3  # three prices give two returns, the minimum for sample volatility


@dataclass(frozen=True)
class PortfolioMetrics:
    """Summary of a target-weight portfolio. All rates are fractions, not percents.

    Attributes:
        daily_returns: simple daily portfolio returns, net of trading costs.
        annualized_return: mean daily return x 252.
        annualized_volatility: daily standard deviation x sqrt(252).
        sharpe_ratio: (annualized return - annual risk-free rate) / volatility;
            NaN when volatility is zero.
        max_drawdown: worst peak-to-trough decline, as a negative fraction.
        annual_turnover: one-way turnover per year (mean daily turnover x 252);
            0.5 means half the portfolio is bought and sold each year.
    """

    daily_returns: pd.Series
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    annual_turnover: float


def analyze_portfolio(
    prices: pd.DataFrame,
    weights: Sequence[float],
    risk_free_rate: float = 0.0,
    rebalance: str = "daily",
    cost_bps: float = 0.0,
) -> PortfolioMetrics:
    """Compute portfolio metrics from adjusted prices, one column per asset.

    ``weights`` follow the column order of ``prices`` and must sum to 1.
    ``risk_free_rate`` is an annual fraction used only for the Sharpe ratio.
    ``rebalance`` sets how often holdings reset to ``weights`` (see
    ``portfolio_returns``); the default ``"daily"`` keeps them fixed.
    ``cost_bps`` is the trading cost in basis points per dollar traded on
    rebalance dates; returns and every metric are net of it.

    Raises:
        ValueError: if prices are too short, contain missing or non-positive
            values, or the weights / risk-free rate / rebalance / cost are
            invalid.
    """
    rate = validate_risk_free_rate(risk_free_rate)
    clean = validate_prices(prices, min_rows=MIN_PRICE_ROWS)
    returns = to_returns(clean)
    daily = portfolio_returns(returns, weights, rebalance, cost_bps)
    turnover = rebalance_turnover(returns, weights, rebalance)
    return PortfolioMetrics(
        daily_returns=daily,
        annualized_return=annualized_return(daily),
        annualized_volatility=annualized_volatility(daily),
        sharpe_ratio=sharpe_ratio(daily, rate),
        max_drawdown=max_drawdown(daily),
        annual_turnover=float(turnover.mean()) * TRADING_DAYS_PER_YEAR,
    )
