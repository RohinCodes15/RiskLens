"""Long-only mean-variance optimization from historical adjusted prices.

Inputs are estimated with the conventions of ``risklens.analytics.metrics``:
simple daily returns from adjusted closes, expected return = mean daily
return x 252, covariance = sample covariance (ddof=1) x 252, and the
risk-free rate is an annual fraction. Portfolios are fully invested and
long-only: weights lie in [0, 1] and sum to 1. A portfolio's reported
return, volatility, and Sharpe ratio equal what ``analyze_portfolio`` gives
for the same prices and weights.

Limitations, stated plainly:
- **Estimation error.** Historical means are very noisy; a few years of
  daily data cannot pin down an asset's expected return. Mean-variance
  optimization magnifies these errors, so maximum-Sharpe weights can swing
  sharply when the price window changes a little and often pile into the
  assets that happened to do best. Covariance estimates are more stable,
  which is one reason minimum-volatility weights (which ignore means) are
  usually more robust.
- **In-sample results.** The weights are fit to the same history used to
  score them, so the reported return, volatility, and Sharpe ratio are
  in-sample and optimistic. They are not a forecast; out-of-sample results
  are typically worse.
"""

from dataclasses import dataclass

import pandas as pd

from risklens.analytics.metrics import MIN_VOLATILITY_OBS, TRADING_DAYS_PER_YEAR
from risklens.data import to_returns
from risklens.validation import validate_prices


class OptimizationError(ValueError):
    """The solver failed to converge to a feasible portfolio.

    Subclasses ``ValueError`` so callers that already report bad inputs to
    the user also report this.
    """


@dataclass(frozen=True)
class SolverDiagnostics:
    """How the optimization went and how trustworthy its inputs were.

    Attributes:
        converged: True when the solver reported success.
        status: scipy's exit code (0 means success for SLSQP).
        message: scipy's exit message.
        iterations: solver iterations used.
        observations: daily returns used to estimate the inputs.
        covariance_rank: numerical rank of the covariance matrix.
        singular_covariance: True when the rank is below the number of
            assets (e.g. duplicate or constant-price assets). The optimum
            is then not unique: other weights give the same objective.
    """

    converged: bool
    status: int
    message: str
    iterations: int
    observations: int
    covariance_rank: int
    singular_covariance: bool


@dataclass(frozen=True)
class OptimizedPortfolio:
    """An optimized long-only portfolio. All rates are annual fractions.

    Attributes:
        objective: ``"min_volatility"`` or ``"max_sharpe"``.
        weights: weight per asset (index = price columns), in [0, 1],
            summing to 1.
        expected_return: weights @ expected annual returns (in-sample).
        volatility: sqrt(weights' covariance weights), annualized.
        sharpe_ratio: (expected_return - risk-free rate) / volatility;
            NaN when volatility is zero.
        diagnostics: solver and covariance diagnostics.
    """

    objective: str
    weights: pd.Series
    expected_return: float
    volatility: float
    sharpe_ratio: float
    diagnostics: SolverDiagnostics


def estimate_inputs(prices: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame, int]:
    """Annualized expected returns, covariance, and return count from prices.

    ``prices`` are aligned adjusted closes (one column per asset, no missing
    values), as returned by ``risklens.data.fetch_prices``.

    Raises:
        ValueError: if prices are invalid (see ``validate_prices``) or give
            no more daily returns than assets, since a sample covariance
            from that few returns is always singular.
    """
    returns = to_returns(validate_prices(prices))
    n_obs, n_assets = returns.shape
    min_obs = max(MIN_VOLATILITY_OBS, n_assets + 1)
    if n_obs < min_obs:
        raise ValueError(
            f"Need at least {min_obs} daily returns to optimize {n_assets} asset(s); got {n_obs}."
        )
    expected = returns.mean() * TRADING_DAYS_PER_YEAR
    covariance = returns.cov() * TRADING_DAYS_PER_YEAR
    return expected.rename("expected_return"), covariance, n_obs
