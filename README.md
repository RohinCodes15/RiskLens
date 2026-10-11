# RiskLens Quant

A portfolio risk analyzer built with Python and Streamlit. Enter tickers and
weights, pull adjusted daily prices from Yahoo Finance, and see the
portfolio's historical return, volatility, Sharpe ratio, and drawdown.

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
- Diversification: HHI concentration, effective number of holdings, and a
  daily-return correlation heatmap.
- Portfolio vs. S&P 500 (SPY) growth chart with ending-return cards.
- **Tail Risk**: a 95%/99% confidence selector, one-day historical VaR and
  CVaR cards (positive values are losses), a histogram of actual daily
  returns with the VaR cutoff marked, and a warning when the sample is too
  small for the selected tail.
- **Simulated futures** tab: seeded Monte Carlo percentile fan chart.
- **Historical scenarios** tab: 2008, 2020, 2022, or custom stress windows,
  with unavailable scenarios explained.
- Bad input, failed downloads, and too-short histories show a readable error
  instead of a traceback.

**Library (`risklens`)**, which goes further than the dashboard:

- Input validation for tickers, weights, risk-free rate, and price tables.
- Price download (yfinance, auto-adjusted closes) and simple daily returns.
- Risk metrics: annualized return and volatility, Sharpe ratio, historical
  VaR, cumulative wealth, drawdown series, max drawdown, and per-asset risk
  contributions.
- Benchmark comparison against SPY and concentration measures (Herfindahl
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

## Run the app

```bash
streamlit run app.py
```

## Tests and checks

```bash
pytest                       # full suite, no network access (yfinance is mocked)
pytest tests/test_smoke.py   # dashboard smoke tests only
ruff check .                 # lint
```

Every test is expected to pass; `-ra` prints the reason for any skip or
expected failure added later.

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
`historical_cvar`, `tail_risk_summary`, `VAR_CONFIDENCE_LEVELS`, and
`TRADING_DAYS_PER_YEAR`. Each function's docstring
gives its units and sign conventions.

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
    metrics.py            Return-based metrics (volatility, Sharpe, VaR, drawdown, ...)
    benchmark.py          Portfolio vs. SPY growth from a common 1.0
    concentration.py      Herfindahl index, effective holdings, correlation
    simulation.py         Seeded Monte Carlo wealth paths (simulate_portfolio)
    stress.py             Historical stress windows (stress_test, custom_scenario)
tests/                    pytest suite (network-free)
pyproject.toml            Package metadata, dependencies, pytest and Ruff config
AGENTS.md                 Architecture, ownership, and coding rules
```

See [AGENTS.md](AGENTS.md) for architecture, ownership, and coding rules.
