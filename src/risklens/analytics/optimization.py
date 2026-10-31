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

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeResult, minimize

from risklens.analytics.metrics import MIN_VOLATILITY_OBS, TRADING_DAYS_PER_YEAR
from risklens.data import to_returns
from risklens.validation import validate_prices, validate_risk_free_rate

SOLVER_METHOD = "SLSQP"
SOLVER_TOLERANCE = 1e-12
SOLVER_MAX_ITERATIONS = 1_000
CONSTRAINT_TOLERANCE = 1e-6  # accepted violation of the solver's constraints
DEFAULT_FRONTIER_POINTS = 40
MIN_FRONTIER_POINTS = 2
MAX_FRONTIER_POINTS = 100  # each point is one solve; bounds run time


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


@dataclass(frozen=True)
class EfficientFrontier:
    """Long-only minimum-volatility portfolios across target returns.

    Attributes:
        points: one row per feasible target, sorted by expected return, with
            columns ``expected_return``, ``volatility``, ``sharpe_ratio``
            (annual fractions; Sharpe is NaN when volatility is zero).
        weights: one row per point (same index as ``points``), one column
            per asset; each row lies in [0, 1] and sums to 1.
        infeasible_targets: targets dropped because the solver failed.
    """

    points: pd.DataFrame
    weights: pd.DataFrame
    infeasible_targets: int


def _validate_points(n_points: object) -> int:
    """Return ``n_points`` as int if it is a whole number in the allowed range."""
    if isinstance(n_points, (bool, np.bool_)) or not isinstance(n_points, (int, np.integer)):
        raise ValueError("n_points must be a whole number.")
    if not MIN_FRONTIER_POINTS <= n_points <= MAX_FRONTIER_POINTS:
        raise ValueError(
            f"n_points must be between {MIN_FRONTIER_POINTS} and {MAX_FRONTIER_POINTS}; "
            f"got {n_points}."
        )
    return int(n_points)


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


def _solve(
    covariance: np.ndarray,
    x0: np.ndarray,
    bounds: list[tuple[float, float | None]],
    directions: np.ndarray,
    targets: np.ndarray,
) -> OptimizeResult:
    """Minimize x' covariance x s.t. directions @ x == targets and ``bounds``.

    ``directions`` has one row per linear equality constraint. The
    covariance is divided by its largest variance first: SLSQP's tolerance
    is absolute, and rescaling the objective leaves the minimizer unchanged.

    Raises:
        OptimizationError: unless SLSQP reports success with a finite,
            feasible solution.
    """
    largest_variance = float(np.max(np.diag(covariance)))
    cov = covariance / largest_variance if largest_variance > 0 else covariance

    def constraint(x: np.ndarray) -> np.ndarray:
        return directions @ x - targets

    def constraint_gradient(x: np.ndarray) -> np.ndarray:
        return directions

    result = minimize(
        lambda x: float(x @ cov @ x),
        x0,
        jac=lambda x: 2.0 * cov @ x,
        method=SOLVER_METHOD,
        bounds=bounds,
        constraints=[{"type": "eq", "fun": constraint, "jac": constraint_gradient}],
        options={"ftol": SOLVER_TOLERANCE, "maxiter": SOLVER_MAX_ITERATIONS},
    )
    x = np.asarray(result.x, dtype=float)
    feasible = (
        np.all(np.isfinite(x))
        and np.all(x >= -CONSTRAINT_TOLERANCE)
        and np.all(np.abs(constraint(x)) <= CONSTRAINT_TOLERANCE)
    )
    if not result.success or not feasible:
        raise OptimizationError(f"Portfolio optimizer did not converge: {result.message}")
    return result


def _portfolio(
    objective: str,
    result: OptimizeResult,
    expected: pd.Series,
    covariance: pd.DataFrame,
    rate: float,
    n_obs: int,
) -> OptimizedPortfolio:
    """Turn solver output into weights summing to 1 plus their in-sample metrics."""
    w = np.clip(np.asarray(result.x, dtype=float), 0.0, None)
    w = w / w.sum()
    cov = covariance.to_numpy()
    ret = float(w @ expected.to_numpy())
    vol = float(np.sqrt(max(float(w @ cov @ w), 0.0)))
    sharpe = float("nan") if np.isclose(vol, 0.0) else (ret - rate) / vol
    rank = int(np.linalg.matrix_rank(cov, hermitian=True))
    diagnostics = SolverDiagnostics(
        converged=bool(result.success),
        status=int(result.status),
        message=str(result.message),
        iterations=int(result.nit),
        observations=n_obs,
        covariance_rank=rank,
        singular_covariance=rank < len(w),
    )
    weights = pd.Series(w, index=expected.index, name="weight")
    return OptimizedPortfolio(objective, weights, ret, vol, sharpe, diagnostics)


def min_volatility_portfolio(
    prices: pd.DataFrame, risk_free_rate: float = 0.0
) -> OptimizedPortfolio:
    """Long-only, fully invested portfolio with the lowest in-sample volatility.

    Minimizes w' covariance w subject to sum(w) = 1 and 0 <= w <= 1, from
    equal weights. The weights ignore expected returns and
    ``risk_free_rate``, which only sets the reported Sharpe ratio (NaN if
    the minimum volatility is zero, e.g. with a constant-price asset).

    Raises:
        ValueError: on invalid prices, too few returns, or an invalid rate.
        OptimizationError: if the solver fails.
    """
    rate = validate_risk_free_rate(risk_free_rate)
    expected, covariance, n_obs = estimate_inputs(prices)
    n = len(expected)
    result = _solve(
        covariance.to_numpy(), np.full(n, 1.0 / n), [(0.0, 1.0)] * n, np.ones((1, n)), np.ones(1)
    )
    return _portfolio("min_volatility", result, expected, covariance, rate, n_obs)


def max_sharpe_portfolio(prices: pd.DataFrame, risk_free_rate: float = 0.0) -> OptimizedPortfolio:
    """Long-only, fully invested portfolio with the highest in-sample Sharpe ratio.

    Solved as the equivalent convex problem: minimize y' covariance y subject
    to (expected - rate) @ y = 1 (rescaled) and y >= 0, then w = y / sum(y). Because it
    is convex, the solution is the global maximum, not a local one, and w
    satisfies 0 <= w <= 1 and sum(w) = 1.

    Raises:
        ValueError: on invalid prices, too few returns, or an invalid rate;
            if no asset's expected return exceeds ``risk_free_rate`` (no
            portfolio has a positive Sharpe ratio, so none is "best"); or if
            a zero-volatility portfolio beats the risk-free rate (the
            Sharpe ratio is then unbounded).
        OptimizationError: if the solver fails.
    """
    rate = validate_risk_free_rate(risk_free_rate)
    expected, covariance, n_obs = estimate_inputs(prices)
    excess = expected.to_numpy() - rate
    if not np.any(excess > 0):
        raise ValueError(
            "No asset's expected return exceeds the risk-free rate, so the maximum-Sharpe "
            "portfolio is undefined. Try the minimum-volatility portfolio."
        )
    direction = excess / excess.max()  # unit scale keeps y near 1; w = y / sum(y) is unchanged
    beats_rate = (excess > 0).astype(float)
    start = beats_rate / float(direction @ beats_rate)  # feasible: direction @ start == 1
    result = _solve(
        covariance.to_numpy(), start, [(0.0, None)] * len(excess), direction[None, :], np.ones(1)
    )
    portfolio = _portfolio("max_sharpe", result, expected, covariance, rate, n_obs)
    if np.isclose(portfolio.volatility, 0.0):
        raise ValueError(
            "A zero-volatility portfolio beats the risk-free rate, so the Sharpe ratio is "
            "unbounded. Remove constant-price assets or raise the risk-free rate."
        )
    return portfolio
