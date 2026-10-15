# RiskLens Quant

A portfolio risk analyzer built with Python and Streamlit. Enter tickers and
weights, pull adjusted daily prices from Yahoo Finance, and see the
portfolio's historical return, volatility, Sharpe ratio, drawdown,
diversification, comparison with the S&P 500 (SPY), one-day VaR and CVaR,
Monte Carlo scenarios, and historical stress tests.

There is no separate backend or database: the Streamlit app calls the
`risklens` package directly.

## Features

**Dashboard (`app.py`)**

- Sidebar inputs: comma-separated tickers (up to 25), a weight per ticker in
  percent (must total 100%), and a start/end date (end date is inclusive).
- **Analyze portfolio** runs the analysis and keeps the result in the session.
- Four risk metric cards: annualized return, annualized volatility, Sharpe
  ratio (0% risk-free rate), and maximum drawdown. Non-finite values show
  as "N/A".
- Historical adjusted-price chart and historical drawdown chart (Plotly).
- **Rolling risk**: rolling volatility, Sharpe ratio, or drawdown over a
  21-, 63-, or 126-trading-day window.
- Diversification: HHI concentration, effective number of holdings, a risk
  attribution chart (each stock's share of portfolio variance next to its
  weight), and a daily-return correlation heatmap.
- Portfolio vs. S&P 500 (SPY) growth chart with ending-return cards.
- **Tail Risk**: a 95%/99% confidence selector, one-day historical VaR and
  CVaR cards (positive values are losses), a histogram of actual daily
  returns with the VaR cutoff marked, and a warning when the sample is too
  small for the selected tail.
- **Simulated futures** tab: seeded Monte Carlo percentile fan chart.
- **Historical scenarios** tab: 2008, 2020, 2022, or custom stress windows,
  with unavailable scenarios explained.
- **Portfolio optimization** (on demand): current, minimum-volatility, and
  maximum-Sharpe weights and metrics side by side, plus an efficient
  frontier chart marking each portfolio and the highest-return frontier
  point no riskier than the current weights.
- Bad input, failed downloads, and too-short histories show a readable error
  instead of a traceback.

**Library (`risklens`)**, which goes further than the dashboard:

- Input validation for tickers, weights, risk-free rate, date ranges, and
  price tables.
- Price download (yfinance, auto-adjusted closes) with date checks before
  any request, and simple daily returns.
- Risk metrics: annualized return and volatility, Sharpe ratio, cumulative
  wealth, drawdown series, max drawdown, and per-asset risk contributions.
- Tail risk: historical VaR and CVaR (Expected Shortfall) at 95% and 99%
  (see [Historical VaR and CVaR](#historical-var-and-cvar)).
- Dated rolling volatility, Sharpe ratio, and drawdown over 21-, 63-, and
  126-day windows (see [Rolling risk metrics](#rolling-risk-metrics)).
- Long-only minimum-volatility and maximum-Sharpe portfolios and the
  efficient frontier (see [Portfolio optimization](#portfolio-optimization)).
- Benchmark comparison against SPY (growth curves plus excess return, beta,
  correlation, and tracking error) and concentration measures (Herfindahl
  index, effective number of holdings, correlation matrix).
- Monte Carlo simulation of future wealth and historical stress testing
  (see [Simulation and stress testing](#simulation-and-stress-testing)).

Conventions: returns are simple daily returns as fractions (0.01 = 1%),
annualized with 252 trading days, and portfolios use fixed weights rebalanced
daily. Drawdowns are negative fractions.

## Installation

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

`[dev]` adds pytest and Ruff. Leave it off (`pip install -e .`) to install
just the app.

Dependency floors in `pyproject.toml` are tested: the full suite passes on
Python 3.11 with the minimum versions (numpy 1.26, pandas 2.2, plotly 5.20,
SciPy 1.11, Streamlit 1.63, yfinance 0.2.40, pytest 8.0) and on current
releases.
Streamlit 1.63 is required by the dashboard tests, whose AppTest checks look
charts up by key.

## Run the app

```bash
streamlit run app.py
```

## Tests and checks

```bash
pytest                                                # full suite, no network (yfinance is mocked)
pytest tests/test_smoke.py tests/test_tail_risk_ui.py tests/test_risk_ui.py  # dashboard tests only
ruff check .                                          # lint
ruff format --check .                                 # formatting
```

Every test is expected to pass. pytest runs with `--strict-markers` and
`xfail_strict`, so a misspelled marker or an expected failure that starts
passing is reported as an error. Ruff's rule set is pinned in
`pyproject.toml` (defaults plus import order, bugs, and modern syntax), so
newer Ruff releases do not change what is enforced.

## Analytics API

The main entry point is `analyze_portfolio`:

```python
analyze_portfolio(prices, weights, risk_free_rate=0.0) -> PortfolioMetrics
```

- `prices`: a DataFrame of adjusted prices, one column per asset, dated
  index, at least 3 rows, all values positive.
- `weights`: one weight per column (in column order), non-negative, summing
  to 1.
- `risk_free_rate`: annual rate as a fraction. It only affects the Sharpe
  ratio.
- Raises `ValueError` for invalid prices, weights, or rate.

`PortfolioMetrics` is a frozen dataclass. All rates are fractions.

| Field | Meaning |
|-------|---------|
| `daily_returns` | `pd.Series` of simple daily portfolio returns |
| `annualized_return` | mean daily return × 252 |
| `annualized_volatility` | sample daily standard deviation × √252 |
| `sharpe_ratio` | (annualized return − risk-free rate) / volatility; NaN if volatility is zero |
| `max_drawdown` | worst peak-to-trough decline (negative) |

Example:

```python
from risklens import analytics, data, validation

tickers = validation.validate_tickers("AAPL, msft, SPY")
weights = validation.validate_weights([0.4, 0.4, 0.2], len(tickers))
prices = data.fetch_prices(tickers, start="2023-01-01", end="2024-01-01")
result = analytics.analyze_portfolio(prices, weights, risk_free_rate=0.04)
print(result.annualized_volatility, result.sharpe_ratio, result.max_drawdown)

drawdowns = analytics.drawdown_series(result.daily_returns)
var_95 = analytics.historical_var(result.daily_returns, confidence=0.95)
```

`risklens.analytics` also exports `portfolio_returns`, `annualized_return`,
`annualized_volatility`, `sharpe_ratio`, `historical_var`,
`cumulative_wealth`, `drawdown_series`, `max_drawdown`, `risk_contributions`,
`compare_to_benchmark`, `herfindahl_index`, `effective_holdings`,
`correlation_matrix`, `simulate_portfolio`, `stress_test`,
`run_stress_tests`, `custom_scenario`, `HISTORICAL_SCENARIOS`,
`historical_cvar`, `tail_risk_summary`, `VAR_CONFIDENCE_LEVELS`,
`benchmark_statistics`, `rolling_volatility`, `rolling_sharpe`,
`rolling_drawdown`, `rolling_max_drawdown`, `rolling_metrics`,
`ROLLING_WINDOWS`, `estimate_inputs`, `min_volatility_portfolio`,
`max_sharpe_portfolio`, `efficient_frontier`, `frontier_point_within_risk`, and
`TRADING_DAYS_PER_YEAR`,
plus the frozen result types `PortfolioMetrics`, `BenchmarkStatistics`,
`MonteCarloResult`, `StressScenario`, `StressResult`, `OptimizedPortfolio`,
`SolverDiagnostics`, and `EfficientFrontier`, and the `OptimizationError` exception. Each function's
docstring gives its units and sign conventions.

`risklens.validation` provides `validate_tickers`, `validate_weights`,
`validate_risk_free_rate`, `validate_prices`, and `validate_date_range`;
`risklens.data` provides `fetch_prices`, `fetch_benchmark_prices`,
`to_returns`, and `DataFetchError`.

Errors: `ValueError` for bad input, `risklens.data.DataFetchError` for
download problems.

## Historical VaR and CVaR

```python
historical_var(returns, confidence=0.95) -> float
historical_cvar(returns, confidence=0.95) -> float
tail_risk_summary(returns, confidence_levels=(0.95, 0.99)) -> pd.DataFrame
```

**Inputs.** Empirical simple daily portfolio returns as fractions, for
example `PortfolioMetrics.daily_returns`. `confidence` is a fraction strictly
between 0 and 1 (0.95 for 95%). Empty input, NaN/inf, returns below −100%,
and non-numeric or out-of-range confidence raise `ValueError`.

**Sign convention.** Both are one-day figures reported as **positive loss
fractions**. A VaR of 0.02 means that on the worst (1 − confidence) of days
the portfolio lost at least 2%. A negative value means even the worst days
were gains.

**Method.**
- VaR = −(the 1 − confidence quantile of daily returns), using NumPy's
  linear interpolation between observed returns.
- CVaR (Expected Shortfall) = −(mean of every observed return at or below
  that quantile). The tail always contains at least the worst day, and CVaR
  is never below VaR.

**Small samples and zero volatility.** With fewer than 1 / (1 − confidence)
returns (under 20 for 95%, under 100 for 99%), the tail is thinner than one
observation, so both figures fall back toward the worst day.
`tail_risk_summary` reports this as `sufficient_sample=False`. Constant
returns give VaR equal to CVaR, both equal to minus that return.

**Limitations.** These are historical, single-day, unconditional figures.
They assume the sample's tail is representative, ignore volatility
clustering, and are not scaled to longer horizons.

## Rolling risk metrics

```python
rolling_volatility(returns, window) -> pd.Series
rolling_sharpe(returns, window, risk_free_rate=0.0) -> pd.Series
rolling_drawdown(returns, window) -> pd.Series
rolling_max_drawdown(returns, window) -> pd.Series
rolling_metrics(returns, window, risk_free_rate=0.0) -> pd.DataFrame
```

**Windows.** `window` is a whole number of trading days, at least 2.
`ROLLING_WINDOWS = (21, 63, 126)` holds the standard choices (about one
month, one quarter, and six months).

**Dates.** Output has exactly the input's index. The value on a date uses the
`window` returns ending on that date, so there is no look-ahead. The first
`window - 1` dates are NaN because they do not have a full window yet.

**Conventions.** The same as the whole-sample metrics: volatility is the
sample standard deviation × √252, Sharpe is (mean daily return × 252 −
`risk_free_rate`) / volatility with the rate as an annual fraction. On the
last full window, each function equals `annualized_volatility`,
`sharpe_ratio`, or `max_drawdown` applied to that slice.

**Rolling drawdown uses a local peak.** `rolling_drawdown` measures each
date's wealth against the highest level within its own window, counting the
level just before the window's first return. It is not the drawdown from the
all-time high; use `drawdown_series` for that. `rolling_max_drawdown` gives
the worst peak-to-trough fall inside each window. Both are fractions ≤ 0.

**Edge cases.**
- A window of constant returns (daily std ≤ 1e-12) has volatility exactly 0
  and Sharpe NaN, matching `sharpe_ratio`.
- Fewer returns than `window`, NaN/inf, returns below −100%, undated or
  unsorted returns, a non-integer or too-small window, and an invalid rate
  raise `ValueError`.
- A −100% day gives drawdown −1.0.

`rolling_metrics` returns all four as columns `volatility`, `sharpe`,
`drawdown`, and `max_drawdown`.

## Portfolio optimization

```python
min_volatility_portfolio(prices, risk_free_rate=0.0) -> OptimizedPortfolio
max_sharpe_portfolio(prices, risk_free_rate=0.0) -> OptimizedPortfolio
efficient_frontier(prices, n_points=40, risk_free_rate=0.0) -> EfficientFrontier
frontier_point_within_risk(frontier, current_volatility) -> int | None
estimate_inputs(prices) -> (expected_returns, covariance, observations)
```

**Inputs.** Aligned adjusted prices, one column per asset, as returned by
`fetch_prices`. Expected returns are mean daily return × 252 and the
covariance is the sample covariance × 252, the same conventions as
`analyze_portfolio`. `risk_free_rate` is an annual fraction.

**Portfolios.** Both are long-only and fully invested: each weight is in
[0, 1] and the weights sum to 1. Both are solved with `scipy.optimize`
(SLSQP). Minimum volatility minimizes w′Σw and ignores expected returns (the
rate only sets its reported Sharpe ratio). Maximum Sharpe is solved as an
equivalent convex problem, so it finds the global optimum, not a local one.

**Result.** `OptimizedPortfolio` holds `weights` (a Series indexed by
ticker), `expected_return`, `volatility`, `sharpe_ratio` (all annual
fractions, equal to `analyze_portfolio` on the same weights), and
`diagnostics`: `converged`, `status`, `message`, `iterations`,
`observations`, `covariance_rank`, and `singular_covariance`.

Example:

```python
from risklens import analytics, data

prices = data.fetch_prices(["AAPL", "MSFT", "SPY"], start="2021-01-01", end="2024-01-01")
safest = analytics.min_volatility_portfolio(prices, risk_free_rate=0.04)
best = analytics.max_sharpe_portfolio(prices, risk_free_rate=0.04)
print(best.weights.round(3), best.sharpe_ratio, best.diagnostics.singular_covariance)
```

**Efficient frontier.** `efficient_frontier` solves `n_points` (2 to 100)
long-only minimum-volatility portfolios at evenly spaced target returns,
from the minimum-volatility portfolio's return up to the best single
asset's. Lower targets are inefficient and left out. `points` has
`expected_return`, `volatility`, and `sharpe_ratio` per point, in
increasing target order; `weights` has the matching weights, one column per
asset. Targets the solver cannot reach are dropped and counted in
`infeasible_targets`; if none can be solved it raises `OptimizationError`.
When every asset has the same expected return, the frontier is the single
minimum-volatility point. For reference markers, plot
`min_volatility_portfolio`, `max_sharpe_portfolio`, and the current weights
(via `analyze_portfolio`) on the same axes.

```python
frontier = analytics.efficient_frontier(prices, n_points=40, risk_free_rate=0.04)
print(frontier.points.head(), frontier.infeasible_targets)
```

**Same risk, more return.** `frontier_point_within_risk(frontier,
current_volatility)` returns the index of the highest-return frontier point
whose volatility is no more than `current_volatility` (an annualized
fraction, plus the solver's 1e-6 tolerance), or `None` if every point is
riskier. Negative, NaN, infinite, or non-numeric budgets raise `ValueError`.

```python
current = analytics.analyze_portfolio(prices, [0.4, 0.4, 0.2])
i = analytics.frontier_point_within_risk(frontier, current.annualized_volatility)
if i is not None:
    print(frontier.points.loc[i], frontier.weights.loc[i])
```

**Edge cases.**
- Fewer daily returns than assets + 1 (the sample covariance is then always
  singular) and invalid prices or rate raise `ValueError`.
- A singular covariance from duplicate or constant-price assets is still
  solved and flagged by `singular_covariance`. The optimum is then not
  unique: other weights reach the same volatility or Sharpe ratio.
- A zero-volatility minimum (a constant-price asset) has Sharpe NaN.
- Maximum Sharpe raises `ValueError` when no asset's expected return beats
  the risk-free rate, or when a zero-volatility portfolio does (the Sharpe
  ratio would be unbounded).
- A solver that fails or returns infeasible weights raises
  `OptimizationError`, a `ValueError` subclass carrying scipy's message.

**Limitations.** Expected returns estimated from a few years of prices are
very noisy, and mean-variance optimization amplifies that error: maximum-
Sharpe weights can swing sharply with small changes to the date range and
tend to concentrate in recent winners. Minimum volatility depends only on
the covariance, which is estimated more reliably. All reported figures are
**in-sample**: the weights are fit to the same history that scores them,
so they overstate what the portfolio would have earned out of sample and
are not a forecast.

## Simulation and stress testing

Both engines produce **hypothetical** results. They apply the portfolio's
current fixed weights to returns; neither is a forecast, and neither
reconstructs the portfolio's actual historical holdings, trades, fees, or
taxes.

### Monte Carlo (`simulate_portfolio`)

```python
simulate_portfolio(daily_returns, horizon_days=252, n_paths=1_000, seed=42) -> MonteCarloResult
```

**Method.** Historical simple daily portfolio returns `r` become log returns
`log(1 + r)`. Their mean (μ) and sample volatility (σ, ddof=1) drive
geometric Brownian motion: each future day's log return is drawn from
Normal(μ, σ) with NumPy's seeded generator, summed along each path, and
converted back with `exp()`. Every path starts at wealth 1.0.

**Output.** `percentile_paths` holds the 5th, 25th, 50th, 75th and 95th
percentile of wealth for each date. Its first row is the last historical
date, where every value is 1.0, and the rows after it are weekdays that keep
the same time of day. `terminal_returns` holds each path's ending wealth
− 1, and `loss_probability` is the share of paths that end below 1.0.

**Guarantees.**
- Same returns, settings and seed always give identical output.
- No look-ahead: only the returns passed in are used, and every simulated
  date comes after the last of them.
- σ is set to exactly 0 only when every historical return is identical, up
  to float rounding (daily standard deviation ≤ 1e-12, the noise left by
  returns computed from constant-growth prices). That gives one
  deterministic curve and a loss probability of 0 or 1.

**Inputs.** At least 2 dated, sorted, finite returns, none at −100% or
below. `horizon_days` must be 1–1,260, `n_paths` 1,000–10,000, and `seed`
0 to 2³²−1. Anything else raises `ValueError`.

**Assumptions and limitations.**
- Returns are treated as i.i.d. and normal in log space, so the model has no
  volatility clustering, regime changes or fat tails. Real crashes can be
  worse than the 5th percentile.
- μ and σ are estimated from a finite sample and treated as known, so short
  histories give unreliable bands.
- Exchange holidays are not removed from future dates.
- The median band is a per-date percentile, not one simulated path.

### Historical stress testing (`stress_test`, `run_stress_tests`)

```python
stress_test(prices, weights, scenario) -> StressResult
run_stress_tests(prices, weights, scenarios=HISTORICAL_SCENARIOS) -> list[StressResult]
custom_scenario(start, end, name="Custom range") -> StressScenario
```

**Scenarios.** `HISTORICAL_SCENARIOS` holds S&P 500 peak-to-trough windows
by closing level. `custom_scenario` builds any other inclusive range.

| Scenario | Start | End |
|----------|-------|-----|
| 2008 financial crisis | 2007-10-09 | 2009-03-09 |
| 2020 COVID crash | 2020-02-19 | 2020-03-23 |
| 2022 bear market | 2022-01-03 | 2022-10-12 |

**Method.**
1. Keep only dates inside the window on which every asset has an actual
   adjusted close. Prices are never forward-filled, backfilled or
   interpolated, so a day any asset is missing is dropped for all assets.
2. Convert the remaining prices to simple daily returns and combine them
   with the fixed weights, rebalanced daily (`portfolio_returns`).
3. Report realized `cumulative_return`, `max_drawdown` (negative) and
   `annualized_volatility` (sample std × √252). These come from the same
   metric functions the dashboard uses.

**Unavailable scenarios.** A result has `available=False`, a plain-language
`reason` and no metrics when:
- an asset's first actual price is more than one weekday after the window
  start (for example, it listed later), or
- its last actual price is more than one weekday before the window end, or
- fewer than 3 common price dates fall inside the window.

Weekends never count against coverage, and one missing weekday is allowed at
each edge for an exchange holiday.

**Inputs.** `prices` is a dated, sorted, unique DataFrame of positive
prices. NaN means "no observation", for example before an asset listed.
Invalid prices, weights or scenarios raise `ValueError`. Scenario dates are
stored as timezone-naive midnight timestamps, and timezone-aware price
indexes are matched by calendar date.

**Limitations.**
- Results are hypothetical, using today's weights and daily rebalancing.
- A dropped day makes the next return span two trading days, which slightly
  understates volatility.
- Within the one-weekday edge allowance, the window can start or end one
  trading day inside the requested dates.
- Survivorship: only tickers that still have data can be tested.

### Usage

```python
from risklens import analytics, data

prices = data.fetch_prices(["SPY", "TLT"], start="2007-01-01", end="2023-01-01")
metrics = analytics.analyze_portfolio(prices, [0.6, 0.4])

sim = analytics.simulate_portfolio(metrics.daily_returns, horizon_days=252, seed=7)
print(sim.loss_probability, sim.percentile_paths.iloc[-1])

for result in analytics.run_stress_tests(prices, [0.6, 0.4]):
    if result.available:
        print(result.scenario.name, result.cumulative_return, result.max_drawdown)
    else:
        print(result.scenario.name, "unavailable:", result.reason)

covid_tail = analytics.custom_scenario("2020-02-19", "2020-06-30", name="COVID and rebound")
print(analytics.stress_test(prices, [0.6, 0.4], covid_tail))
```

`fetch_prices` keeps only dates where every ticker has a price. Fetch from
before the earliest scenario so coverage can be checked, and expect older
scenarios to be unavailable for recently listed tickers.

## File structure

```
app.py                    Streamlit dashboard
src/risklens/
  validation.py           Ticker, weight, risk-free rate, price, and date checks
  data.py                 Price download (yfinance), SPY benchmark, daily returns
  analytics/
    engine.py             analyze_portfolio and PortfolioMetrics
    metrics.py            Return-based metrics (volatility, Sharpe, VaR/CVaR, drawdown, ...)
    rolling.py            Dated rolling volatility, Sharpe, and drawdown
    optimization.py       Long-only min-volatility and max-Sharpe weights (SciPy)
    benchmark.py          Portfolio vs. SPY growth and benchmark statistics
    concentration.py      Herfindahl index, effective holdings, correlation
    simulation.py         Seeded Monte Carlo wealth paths (simulate_portfolio)
    stress.py             Historical stress windows (stress_test, custom_scenario)
tests/                    pytest suite (network-free); test_smoke.py,
                          test_tail_risk_ui.py, and test_risk_ui.py drive the
                          dashboard with AppTest
pyproject.toml            Package metadata, dependencies, pytest and Ruff config
AGENTS.md                 Architecture, ownership, and coding rules
LICENSE                   MIT license
```

See [AGENTS.md](AGENTS.md) for architecture, ownership, and coding rules.
