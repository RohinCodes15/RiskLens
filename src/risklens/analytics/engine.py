"""Portfolio risk engine: adjusted prices + weights -> summary metrics.

Expects adjusted close prices (splits and dividends applied), as returned by
``risklens.data.fetch_prices``, so returns reflect total return.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from risklens.analytics.metrics import (
    annualized_return,
    annualized_volatility,
    max_drawdown,
    portfolio_returns,
    sharpe_ratio,
)
from risklens.data import to_returns

MIN_PRICE_ROWS = 2


@dataclass(frozen=True)
class PortfolioMetrics:
    """Summary of a fixed-weight portfolio. All rates are fractions, not percents.

    Attributes:
        daily_returns: simple daily portfolio returns.
        annualized_return: mean daily return x 252.
        annualized_volatility: daily standard deviation x sqrt(252).
        sharpe_ratio: (annualized return - annual risk-free rate) / volatility;
            NaN when volatility is zero.
        max_drawdown: worst peak-to-trough decline, as a negative fraction.
    """

    daily_returns: pd.Series
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float


def analyze_portfolio(
    prices: pd.DataFrame,
    weights: Sequence[float],
    risk_free_rate: float = 0.0,
) -> PortfolioMetrics:
    """Compute portfolio metrics from adjusted prices, one column per asset.

    ``weights`` follow the column order of ``prices`` and must sum to 1.
    ``risk_free_rate`` is an annual fraction used only for the Sharpe ratio.

    Raises:
        ValueError: if prices are too short, contain missing or non-positive
            values, or the weights / risk-free rate are invalid.
    """
    # TODO(human): validate prices, build daily returns, return PortfolioMetrics.
    raise NotImplementedError("analyze_portfolio body is left for the human to write.")
