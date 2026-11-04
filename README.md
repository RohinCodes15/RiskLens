# RiskLens Quant

A portfolio risk analyzer built with Python and Streamlit. Enter holdings as
percent weights, share counts, or dollar values (or import them from a CSV
file), pull adjusted daily prices from Yahoo Finance, and see the
portfolio's historical return, volatility, Sharpe ratio, drawdown,
diversification, comparison with the S&P 500 (SPY), one-day VaR and CVaR,
Monte Carlo scenarios, and historical stress tests.

There is no separate backend or database: the Streamlit app calls the
`risklens` package directly.

## Features

**Dashboard (`app.py`)**

- Sidebar inputs: comma-separated tickers (up to 25); holdings per ticker as
  percent weights (must total 100%), share counts, or dollar values; a
  start/end date (end date is inclusive); a rebalancing frequency (daily,
  monthly, quarterly, annually, or never); and a trading cost in basis points
  per dollar traded. Shares are valued at each stock's last close in the
  selected period to get the weights.
- **Import holdings from CSV**: upload a file with `ticker` and `shares` or
  `value` columns instead of typing holdings. Every bad row is reported by
  line number and blocks the analysis until fixed; see
  [Holdings input](#holdings-input).
- **Dollar amounts**: holdings in shares or dollars give the portfolio value;
  with percent weights you can enter it (optional). When it is known, the
  maximum drawdown, one-day VaR and CVaR, and stress-test return and
  drawdown cards also show the change in dollars, e.g. "-$4,820".
- The risk cards, rolling risk, tail risk, SPY comparison, and stress tests
  all follow the chosen rebalancing and are net of trading costs; the
  snapshot shows annual turnover. Optimization compares allocations with
  daily rebalancing and no costs, and says so when that differs from your
  settings.
- **Analyze portfolio** runs the analysis and keeps the result in the session.
- Six risk metric cards: annualized return, annualized volatility, Sharpe
  ratio (0% risk-free rate), maximum drawdown, Sortino ratio, and Calmar
  ratio. Non-finite values show as "N/A".
- Historical adjusted-price chart and historical drawdown chart (Plotly).
- **Where risk comes from**: Fama-French market, size, value and momentum
  betas with annualized alpha and R², plus sector and country tables of
  weight and share of risk. Loaded on demand; see
  [Factor and sector exposure](#factor-and-sector-exposure).
- **Rolling risk**: rolling volatility, Sharpe ratio, or drawdown over a
  21-, 63-, or 126-trading-day window.
- Diversification: HHI concentration, effective number of holdings, a risk
  attribution chart (each holding's share of the risk of the portfolio you
  actually hold, after your rebalancing and trading costs, next to its
  weight; trading costs get their own bar), and a daily-return correlation
  heatmap.
- Portfolio vs. S&P 500 (SPY) growth chart with ending-return cards, plus
  information ratio and up- and down-market capture cards.
- **Tail Risk**: a 95%/99% confidence selector, one-day historical VaR and
  CVaR cards next to normal and Cornish-Fisher VaR (positive values are
  losses), a histogram of actual daily returns with the VaR cutoff marked, a
  warning when the sample is too small for the selected tail, and a **VaR
  backtest** table: each method's breaches over the days after a 63-, 126-,
  or 252-day estimation window, with the Kupiec test's verdict.
- **Volatility forecast**: historical, EWMA (RiskMetrics, λ = 0.94), and
  GARCH(1,1) volatility cards, with the GARCH forecast averaged over a
  horizon you choose, and a chart of each model's estimate on each date. See
  [Volatility forecasts](#volatility-forecasts).
- **Simulated futures** tab: seeded Monte Carlo percentile fan chart, with
  normal, Student-t (fat tails), or bootstrap (resampled past days) returns.
- **Historical scenarios** tab: 2008, 2020, 2022, or custom stress windows,
  with unavailable scenarios explained.
- **What-if trade** tab: sell part of one holding, buy another ticker (held
  or new), and compare the weights, return, volatility, Sharpe, Sortino,
  drawdown, VaR, CVaR, and turnover before and after, plus the trade's
  one-time cost. See
  [What-if trades and custom shocks](#what-if-trades-and-custom-shocks).
- **Custom shocks** tab: enter moves such as Technology −20% or Long-term
  bonds +5% and see the estimated portfolio move (in dollars too when the
  portfolio value is known), with each holding's move and betas.
- **Portfolio optimization** (on demand): current, minimum-volatility, and
  maximum-Sharpe weights and metrics side by side, with each one's turnover
  from your current weights and an optional turnover limit, plus an
  efficient frontier chart marking each portfolio and the highest-return
  frontier point no riskier than the current weights.
- **Download report**: an HTML page (tables plus wealth and drawdown charts,
  viewable offline and printable to PDF) and a zip of CSV tables with the
  settings, metrics, holdings, SPY statistics, and daily returns. See
  [Report export](#report-export).
- Bad input, failed downloads, and too-short histories show a readable error
  instead of a traceback.

**Library (`risklens`)**, which goes further than the dashboard:

- Input validation for tickers, weights, risk-free rate, date ranges, and
  price tables.
- Price download (yfinance, auto-adjusted closes) with date checks before
  any request, either aligned to shared dates or as per-ticker history that
  keeps each ticker's own coverage, and simple daily returns.
- Holdings: CSV parsing with per-line errors, and share counts or dollar
  values converted to weights (see [Holdings input](#holdings-input)).
- Portfolio returns rebalanced daily, monthly, quarterly, annually, or never
  (buy-and-hold); see [Rebalancing and trading costs](#rebalancing-and-trading-costs).
- Risk metrics: annualized return and volatility, Sharpe, Sortino, and
  Calmar ratios, cumulative wealth, drawdown series, max drawdown, and
  per-asset risk contributions, also for rebalanced, cost-adjusted portfolios.
- Tail risk: historical VaR and CVaR (Expected Shortfall) at 95% and 99%
  (see [Historical VaR and CVaR](#historical-var-and-cvar)), plus normal and
  Cornish-Fisher VaR, rolling out-of-sample VaR, and a Kupiec backtest (see
  [VaR models and backtesting](#var-models-and-backtesting)).
- Dated rolling volatility, Sharpe ratio, and drawdown over 21-, 63-, and
  126-day windows (see [Rolling risk metrics](#rolling-risk-metrics)).
- EWMA and GARCH(1,1) volatility forecasts (see
  [Volatility forecasts](#volatility-forecasts)).
- Long-only minimum-volatility and maximum-Sharpe portfolios, optionally
  within a turnover limit, and the efficient frontier (see
  [Portfolio optimization](#portfolio-optimization)).
- Report export as CSV tables and an HTML page (see
  [Report export](#report-export)).
- Benchmark comparison against SPY (growth curves plus excess return, beta,
  correlation, tracking error, information ratio, and up/down capture) and
  concentration measures (Herfindahl
  index, effective number of holdings, correlation matrix).
- Monte Carlo simulation of future wealth with normal, Student-t, or
  bootstrap daily returns, and historical stress testing
  (see [Simulation and stress testing](#simulation-and-stress-testing)).
- What-if trades compared on the same prices, and custom shocks to market
  proxies passed to each holding through its betas (see
  [What-if trades and custom shocks](#what-if-trades-and-custom-shocks)).

Conventions: returns are simple daily returns as fractions (0.01 = 1%),
annualized with 252 trading days, and portfolios reset to their target weights
daily unless another rebalance frequency is chosen (see
[Rebalancing and trading costs](#rebalancing-and-trading-costs)). Drawdowns are negative fractions.

## Installation

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

`[dev]` adds pytest, pytest-cov, and Ruff. Leave it off (`pip install -e .`) to install
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
pytest tests/test_smoke.py tests/test_tail_risk_ui.py tests/test_risk_ui.py tests/test_holdings_ui.py tests/test_risk_metrics_ui.py tests/test_risk_sources_ui.py tests/test_what_if_ui.py tests/test_shocks_ui.py tests/test_volatility_ui.py tests/test_simulation_tails_ui.py  # dashboard tests only
pytest --cov                                          # with branch coverage of src/risklens
ruff check .                                          # lint
ruff format --check .                                 # formatting
python benchmarks/simulation_memory.py                # Monte Carlo peak memory (not run by pytest)
```

Every test is expected to pass. pytest runs with `--strict-markers` and
`xfail_strict`, so a misspelled marker or an expected failure that starts
passing is reported as an error. Ruff's rule set is pinned in
`pyproject.toml` (defaults plus import order, bugs, and modern syntax), so
newer Ruff releases do not change what is enforced.

## Analytics API

The main entry point is `analyze_portfolio`:

```python
analyze_portfolio(
    prices, weights, risk_free_rate=0.0, rebalance="daily", cost_bps=0.0
) -> PortfolioMetrics
```

- `prices`: a DataFrame of adjusted prices, one column per asset, dated
  index, at least 3 rows, all values positive.
- `weights`: one weight per column (in column order), non-negative, summing
  to 1.
- `risk_free_rate`: annual rate as a fraction. It only affects the Sharpe
  and Sortino ratios.
- `rebalance`: how often holdings reset to `weights`; one of
  `REBALANCE_FREQUENCIES`.
- `cost_bps`: trading cost in basis points per dollar traded on rebalance
  dates. Every metric below is net of it.
- Raises `ValueError` for invalid prices, weights, rate, rebalance, or cost.

`PortfolioMetrics` is a frozen dataclass. All rates are fractions.

| Field | Meaning |
|-------|---------|
| `daily_returns` | `pd.Series` of simple daily portfolio returns, net of trading costs |
| `annualized_return` | mean daily return × 252 |
| `annualized_volatility` | sample daily standard deviation × √252 |
| `sharpe_ratio` | (annualized return − risk-free rate) / volatility; NaN if volatility is zero |
| `max_drawdown` | worst peak-to-trough decline (negative) |
| `sortino_ratio` | (annualized return − risk-free rate) / annualized downside deviation; NaN without a day below the risk-free rate |
| `calmar_ratio` | compound annual growth rate / \|max drawdown\|; NaN without a drawdown |
| `annual_turnover` | one-way turnover per year: mean daily turnover × 252 (0.5 = half the portfolio traded) |

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

`risklens.analytics` also exports `portfolio_returns`, `rebalance_turnover`, `annualized_return`,
`annualized_volatility`, `sharpe_ratio`, `historical_var`,
`cumulative_wealth`, `drawdown_series`, `max_drawdown`, `risk_contributions`,
`factor_exposure`, `FactorExposure`, `group_breakdown`, `FACTOR_COLUMNS`,
`compare_to_benchmark`, `herfindahl_index`, `effective_holdings`,
`correlation_matrix`, `simulate_portfolio`, `stress_test`,
`run_stress_tests`, `custom_scenario`, `HISTORICAL_SCENARIOS`,
`trade_weights`, `trade_cost`, `compare_portfolios`, `COMPARISON_METRICS`,
`shock_impact`, `SHOCK_PROXIES`, `MIN_SHOCK_OBS`,
`historical_cvar`, `tail_risk_summary`, `VAR_CONFIDENCE_LEVELS`,
`benchmark_statistics`, `rolling_volatility`, `rolling_sharpe`,
`rolling_drawdown`, `rolling_max_drawdown`, `rolling_metrics`,
`ROLLING_WINDOWS`, `ewma_volatility`, `fit_garch`, `garch_forecast`,
`horizon_volatility`, `EWMA_LAMBDA`, `MIN_GARCH_OBS`, `MAX_FORECAST_DAYS`,
`estimate_inputs`, `min_volatility_portfolio`,
`max_sharpe_portfolio`, `efficient_frontier`, `frontier_point_within_risk`,
`sortino_ratio`, `calmar_ratio`, `normal_var`, `cornish_fisher_var`,
`rolling_var`, `kupiec_test`, `var_backtest`, `VAR_METHODS`,
`VAR_BACKTEST_WINDOWS`, `KUPIEC_SIGNIFICANCE`, and
`TRADING_DAYS_PER_YEAR`, `REBALANCE_FREQUENCIES`,
plus the frozen result types `PortfolioMetrics`, `BenchmarkStatistics`,
`MonteCarloResult`, `GarchFit`, `StressScenario`, `StressResult`, `ShockImpact`,
`OptimizedPortfolio`,
`SolverDiagnostics`, and `EfficientFrontier`, and the `OptimizationError` exception. Each function's
docstring gives its units and sign conventions.

`risklens.validation` provides `validate_tickers`, `validate_weights`,
`validate_risk_free_rate`, `validate_cost_bps`, `validate_prices`, `validate_price_history`, and
`validate_date_range`; `risklens.data` provides `fetch_prices`,
`fetch_price_history`, `fetch_benchmark_prices`, `to_returns`, and
`DataFetchError`; `risklens.holdings` provides `parse_holdings_csv`,
`holdings_to_weights`, and `HOLDING_KINDS`.

**Two ways to fetch prices.**

| Function | Dates kept | Missing prices | Use for |
|----------|------------|----------------|---------|
| `fetch_prices` | only dates every ticker traded | rows dropped; raises if any ticker has no data | metrics, benchmark, optimization |
| `fetch_price_history` | every date at least one ticker traded | NaN, never filled; a ticker with no data is an all-NaN column | stress testing and other coverage checks |

Both take `(tickers, start, end=None)`, download auto-adjusted closes, keep
the ticker order, and raise `DataFetchError` for failed or unusable
downloads. `fetch_prices` is unchanged; on the dates every ticker shares,
the two return the same prices.

Errors: `ValueError` for bad input, `risklens.data.DataFetchError` for
download problems.

## Holdings input

```python
parse_holdings_csv(content) -> tuple[str, pd.Series]
holdings_to_weights(amounts, kind, prices) -> tuple[np.ndarray, float]
```

Both live in `risklens.holdings`. A holdings CSV has a header row with a
`ticker` column and exactly one of `shares` or `value` (dollars), in any
letter case, then one row per stock (up to 25):

```csv
ticker,shares
AAPL,10
MSFT,4.5
```

```csv
Ticker,Value
AAPL,"$12,500.00"
TLT,4000
```

Other columns are ignored and blank lines are skipped, so a brokerage export
with extra columns works once its headers are renamed. Amounts may have a
leading `$` and thousands separators; zero is allowed, negatives are not.
UTF-8 files with or without Excel's byte-order mark are accepted.
`parse_holdings_csv` returns the column used (`"shares"` or `"value"`) and
the amounts indexed by upper-case ticker in file order. A bad file raises one
`ValueError` that lists every problem by line, for example
`Line 3: Shares must be a number; got 'ten'. Line 5: AAPL is already listed on line 2.`

`holdings_to_weights` turns share counts or dollar values into weights in
the order of `prices.columns` and returns the portfolio's total value in
dollars. Shares are valued at the last row of `prices`. These are adjusted
closes, which equal the actual closes when the period ends today; for an
earlier end date they are the split- and dividend-adjusted closes on that
date. It raises `ValueError` when the holdings do not match the price
columns, an amount is negative or not finite, or every holding is zero.

**Dollar amounts.** The dashboard multiplies each percentage by the portfolio
value: one-day VaR and CVaR become the dollar change on a bad day, and the
maximum drawdown and stress-test return and drawdown become the dollar
change if that history repeated on today's portfolio. Amounts are signed
(negative means a loss) and rounded to whole dollars.

## Rebalancing and trading costs

```python
portfolio_returns(returns, weights, rebalance="daily", cost_bps=0.0) -> pd.Series
rebalance_turnover(returns, weights, rebalance="daily") -> pd.Series
```

`rebalance` is one of `REBALANCE_FREQUENCIES`:

| Value | Behavior |
|-------|----------|
| `"daily"` (default) | weights reset every day; each return is `returns @ weights` |
| `"monthly"`, `"quarterly"`, `"annual"` | holdings drift with prices and reset to `weights` on the first return date of each calendar month, quarter, or year |
| `"never"` | buy-and-hold: `weights` is only the starting allocation |

The first return date always starts at `weights`. Calendar frequencies need
returns on a sorted, unique `DatetimeIndex` (time zones are fine).

**Turnover.** On a rebalance date, holdings that drifted since the last
reset are traded back to `weights` before that date's return.
`rebalance_turnover` gives the one-way turnover on each date: half the sum
of absolute weight changes, which equals the fraction of the portfolio
bought (and sold). It is 0 on dates without a reset and on the first date,
because the initial purchase is not counted.

**Trading costs.** `cost_bps` is the cost in basis points per dollar bought
or sold (5 = 0.05%), covering commission and spread. On each rebalance date
the portfolio pays `cost_bps / 10,000 × 2 × turnover` of its value, so the
net return is `(1 − cost) × (1 + gross return) − 1`. The default 0 charges
nothing, buy-and-hold never pays, and `validate_cost_bps` rejects negative,
non-finite, or above-1,000 bps values.

Example: 50/50 weights after one asset doubles are 2/3 and 1/3. Resetting
them sells 1/6 of the portfolio and buys 1/6 (turnover 1/6); at 100 bps
that costs 1/300 of the portfolio.

`analyze_portfolio`, `compare_to_benchmark`, `benchmark_statistics`,
`stress_test`, and `run_stress_tests` take the same `rebalance` and
`cost_bps` arguments and pass them through, so every return-based metric is
net of costs. `PortfolioMetrics.annual_turnover` reports mean daily
turnover × 252. `rebalanced_risk_contributions` and `group_breakdown` take
them too (see [Factor and sector exposure](#factor-and-sector-exposure)).
Optimization still assumes daily rebalancing without costs; its turnover
limit only caps the trade away from your current weights.
`simulate_portfolio` resamples whatever daily returns it is given; the
dashboard gives it the portfolio's returns after rebalancing and costs, but
does not simulate holdings one by one.

## Risk-adjusted ratios

```python
sortino_ratio(returns, risk_free_rate=0.0) -> float
calmar_ratio(returns) -> float
benchmark_statistics(...).information_ratio / .upside_capture / .downside_capture
```

All take simple daily returns (fractions); `analyze_portfolio` reports the
first two and `benchmark_statistics` the rest.

| Ratio | Definition | Reads as |
|-------|------------|----------|
| Sortino | (mean daily return × 252 − risk-free rate) / (√(mean of squared daily shortfalls below risk-free ÷ 252) × √252), counting every day, so up days add zero shortfall | Sharpe with only losses counted as risk; NaN without a down day |
| Calmar | compound annual growth (final wealth^(252 / days) − 1) / \|max drawdown\| | yearly growth per unit of worst decline; NaN without a drawdown |
| Information ratio | (portfolio − SPY annualized return) / tracking error | excess return per unit of risk relative to SPY; NaN when the portfolio tracks SPY exactly |
| Upside capture | geometric mean daily return on days SPY rose ÷ SPY's on those days | above 1.0: gained more than SPY on up days |
| Downside capture | the same on days SPY fell | below 1.0: lost less than SPY on down days (lower is better); negative: gained while SPY fell |

Calmar compounds growth, the usual convention, unlike the arithmetic
annualized return used elsewhere. Capture follows Morningstar's
geometric-mean method on daily data; days when SPY moved less than 1e-12
count as neither up nor down, and a ratio is NaN when there are no such days.
Every figure is net of the chosen rebalancing and trading costs.

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

## VaR models and backtesting

```python
normal_var(returns, confidence=0.95) -> float
cornish_fisher_var(returns, confidence=0.95) -> float
rolling_var(returns, window, confidence=0.95, method="historical") -> pd.Series
kupiec_test(breaches, days, confidence) -> tuple[float, float]
var_backtest(returns, window, confidence=0.95) -> pd.DataFrame
```

These live in `risklens.analytics.value_at_risk` and use the sign convention
of `historical_var`: one-day losses as positive fractions.

**Models.**
- `normal_var` = −(mean + z × standard deviation), where z is the standard
  normal quantile at 1 − confidence (−1.645 at 95%, −2.326 at 99%) and the
  standard deviation is the sample one (ddof=1). Needs 2 returns.
- `cornish_fisher_var` replaces z with
  z + (z² − 1)S/6 + (z³ − 3z)K/24 − (2z³ − 5z)S²/36, where S is the sample
  skewness and K the sample excess kurtosis (bias-corrected, as
  `pandas.Series.skew` and `.kurt` compute them). Needs 4 returns. Negative
  skew raises the loss. Fat tails raise it at 99% but can lower it at 95%,
  where the (z³ − 3z) term is positive. The expansion is only a valid
  quantile while it rises from z to the median and stays below the mean;
  outside that range, typically after one huge outlier such as a +25% or
  −40% day, it falls back to `normal_var` instead of reporting a near-zero
  loss.
- Constant returns give both models minus that return.

**Backtest.** `rolling_var` forecasts each day's VaR from the `window`
returns strictly before it, so a forecast never sees the day it is scored
on; `method` is one of `VAR_METHODS` (`"historical"`, `"normal"`,
`"cornish_fisher"`). A breach is a day whose return is below −VaR.
`var_backtest` counts breaches for every method over the same days and
returns, indexed by method, `days`, `breaches`, `expected_breaches`
(days × (1 − confidence)), `breach_rate`, the Kupiec `statistic` and
`p_value`, and `sufficient_sample`, False when fewer than one breach is
expected (the dashboard then shows "Too few test days to judge").

**Kupiec test.** `kupiec_test` is the proportion-of-failures likelihood
ratio −2 ln[(1 − p)^(n−x) p^x / ((1 − x/n)^(n−x) (x/n)^x)] with p = 1 −
confidence, x breaches, and n days, compared with a chi-square distribution
with one degree of freedom. A p-value below `KUPIEC_SIGNIFICANCE` (5%)
rejects the VaR: too many breaches mean it understated losses, too few that
it overstated them. With few test days the test has little power: 255 days
at 99% expect only 2.55 breaches.

The dashboard backtests with a 63-, 126-, or 252-day window
(`VAR_BACKTEST_WINDOWS`, default 126, so a one-year period still leaves
about 125 test days) at the Tail Risk confidence level. A window with
under five days beyond the cutoff (every window at 99%) leaves historical
VaR noisy and prone to too many breaches, and the dashboard says so.

## Factor and sector exposure

**Load factor and sector data** downloads two extra sources, so it runs only
when you ask:

- **Factors** (`data.fetch_factors`): daily Fama-French 3 factors (`Mkt-RF`,
  `SMB`, `HML`), Carhart momentum (`Mom`) and the risk-free rate (`RF`) from the
  [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html),
  converted from percent to fractions. The library lags by a month or more,
  so the latest days of your period may be left out.
- **Sectors and countries** (`data.fetch_classifications`): from each ticker's
  Yahoo Finance profile. Funds have no sector and are grouped by quote type
  (e.g. `ETF`); a profile that cannot be loaded shows as `Unknown`.

`factor_exposure(returns, factors)` regresses daily portfolio returns minus
`RF` on the four factors by ordinary least squares:

```
r_p − RF = α + β_mkt·(Mkt−RF) + β_smb·SMB + β_hml·HML + β_mom·Mom + ε
```

It returns a `FactorExposure` with the betas, alpha annualized as the daily
intercept × 252, R² (the share of excess-return variance the factors
explain), and the dates used. It needs at least `MIN_FACTOR_OBS` (60) days
shared with the factor data. The portfolio returns follow the selected
rebalancing and are net of trading costs.

`group_breakdown(returns, weights, labels, rebalance="daily", cost_bps=0.0)`
sums allocation weights and risk shares by sector or country. The risk
shares come from `rebalanced_risk_contributions`, the same as the Risk
attribution chart, so they follow your rebalancing and trading cost; with
costs, a `Trading costs` group (weight 0) holds the cost share.

### Risk shares with rebalancing and costs (`rebalanced_risk_contributions`)

```python
rebalanced_risk_contributions(returns, weights, rebalance="daily", cost_bps=0.0) -> pd.Series
```

Each day's net portfolio return, as `portfolio_returns` computes it, splits
exactly into one piece per holding (the weight it held that morning times
its return) plus a cost piece, −cost × (1 + gross return). Between
rebalances the held weights drift with prices. A piece's share of risk is
its sample covariance with the portfolio's daily return divided by the
portfolio's variance, so the shares sum to 1:

```
share_i = cov(h_i,t · r_i,t, r_p,t) / var(r_p,t)
```

With daily rebalancing and no costs the held weights never change and this
equals `risk_contributions` (weight × the asset's covariance with the
portfolio ÷ portfolio variance). The `COST_LABEL` (`"Trading costs"`) row
appears only when `cost_bps` > 0; it is usually close to 0 and can be
negative. It needs at least 2 returns and raises `ValueError` when the
portfolio's variance is zero.

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

## Volatility forecasts

```python
ewma_volatility(returns, decay=0.94) -> pd.Series
fit_garch(returns) -> GarchFit
garch_forecast(fit, horizon_days) -> pd.Series
horizon_volatility(forecast) -> float
```

The dashboard's **Volatility forecast** section, below Tail Risk, uses the
portfolio's daily returns after your rebalancing and trading cost. It shows
four cards (historical volatility, EWMA next-day volatility, GARCH
volatility over a horizon you choose from 1 to 252 trading days, default 21,
and GARCH long-run volatility) and a chart of the EWMA and GARCH estimates
on each date.

**Dates.** Both models return a series with the input's dates. The value on
a date uses returns up to and including that date and estimates the next
day's volatility, so there is no look-ahead and the last value is the
next-day forecast. Every volatility is annualized (daily × √252).

**EWMA (RiskMetrics).** `σ²_t = λ·σ²_{t−1} + (1 − λ)·r_t²` with
`λ = EWMA_LAMBDA = 0.94`, started at `σ²_0 = r_0²`, with no mean removed, as
in RiskMetrics. Its forecast is the same for every future day.

**GARCH(1,1).** On demeaned returns `e_t = r_t − mean`, with variance
targeting:

```
σ²_{t+1} = ω + α·e_t² + β·σ²_t,    ω = v̄·(1 − α − β),    σ²_0 = v̄
```

where `v̄` is the sample variance. `fit_garch` picks α and β by maximizing
the Gaussian likelihood with SciPy's SLSQP, keeping α, β ≥ 0 and
α + β < 1. It returns a `GarchFit` with ω, α, β, `persistence` (α + β), the
mean, the dated `conditional_volatility`, `long_run_volatility`
(√(v̄ × 252)), the log-likelihood, and the number of returns. It needs at
least `MIN_GARCH_OBS` (200) returns and raises `ValueError` for constant
returns or when the optimizer does not converge; the dashboard then shows
EWMA only and says why.

`garch_forecast(fit, horizon_days)` gives the volatility for each of the
next 1 to `MAX_FORECAST_DAYS` (252) days. Day h has variance
`v̄ + (α + β)^(h−1)·(σ²_next − v̄)`, so the forecast starts at the next-day
value and moves toward the long-run level, more slowly the closer
persistence is to 1. `horizon_volatility(forecast)` gives one number for the
whole horizon: the square root of the average daily variance.

**Limitations.** One fit on the whole sample with a normal likelihood, so
fat tails are not modeled and the parameters are treated as known. These are
estimates from past returns, not predictions.

## Portfolio optimization

```python
min_volatility_portfolio(
    prices, risk_free_rate=0.0, *, current_weights=None, max_turnover=None
) -> OptimizedPortfolio
max_sharpe_portfolio(
    prices, risk_free_rate=0.0, *, current_weights=None, max_turnover=None
) -> OptimizedPortfolio
efficient_frontier(prices, n_points=40, risk_free_rate=0.0, *, min_volatility=None) -> EfficientFrontier
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

**Turnover limit.** Pass `current_weights` (summing to 1) and `max_turnover`
(a fraction from 0 to 1) together to consider only weights within that
one-way turnover of the current ones: 0.5 × Σ|w − current| ≤
`max_turnover`, the share of the portfolio bought, which equals the share
sold (`one_way_turnover(before, after)` measures it). The limit is added
with extra variables uᵢ ≥ |wᵢ − currentᵢ|, so every constraint stays linear
and both problems stay convex: the result is the true minimum volatility or
maximum Sharpe ratio within the limit. A limit of 0 returns the current
weights, and 1 never binds; `validate_turnover_limit` checks the value. The
efficient frontier is never limited. In the dashboard, **Turnover limit (%
of portfolio)** sets it (100% means no limit), and the table shows each
column's turnover from your current weights.

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
(via `analyze_portfolio`) on the same axes. If you already have
`min_volatility_portfolio(prices)`, pass it as `min_volatility=` so the
frontier does not solve it again; a result from other prices or assets
raises `ValueError`.

```python
safest = analytics.min_volatility_portfolio(prices)
frontier = analytics.efficient_frontier(
    prices, n_points=40, risk_free_rate=0.04, min_volatility=safest
)
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
simulate_portfolio(
    daily_returns, horizon_days=252, n_paths=1_000, seed=42, distribution="normal"
) -> MonteCarloResult
```

**Method.** Historical simple daily portfolio returns `r` become log returns
`log(1 + r)`, with mean μ and sample volatility σ (ddof=1). Each future
day's log return is drawn with NumPy's seeded generator, summed along each
path, and converted back with `exp()`. Every path starts at wealth 1.0.
`distribution` (one of `DISTRIBUTIONS` in `risklens.analytics.simulation`)
picks the draws:

- `"normal"` (default): Normal(μ, σ), geometric Brownian motion. Results are
  the same as before this option existed, for the same seed.
- `"student_t"`: μ + σ·t·√((df − 2)/df), a Student-t with the same mean and
  volatility but fatter tails. The degrees of freedom match the history's
  bias-corrected excess kurtosis k: df = 4 + 6/k. Fewer than 4 returns, or
  k ≤ 0 (no fat tails), raises `ValueError`.
- `"bootstrap"`: past daily log returns drawn with replacement, which keeps
  their real skew and fat tails but never produces a day worse than the
  worst past day.

`MonteCarloResult` also reports `distribution` and `degrees_of_freedom` (NaN
unless Student-t). The dashboard's **Return distribution** menu picks the
model. Paths come from the portfolio's past daily returns, so in the
dashboard they already reflect your rebalancing and trading cost; holdings
are not simulated one by one.

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

**Memory.** One `n_paths × horizon_days` float64 array holds every path. It
is transformed in place (draws → cumulative log wealth → wealth) and
partitioned in place for the percentiles; the all-1.0 start row is added to
the small band table instead of to every path. Peak traced memory for
10,000 × 1,260 measured with `python benchmarks/simulation_memory.py`:

| Version | Peak traced memory | Full arrays |
|---------|--------------------|-------------|
| Before (separate draw, cumsum, exp, `hstack` and percentile copies) | 403.7 MB | 4.00 |
| After (one buffer reused in place) | 101.2 MB | 1.00 |

Results are bit-identical for the same seed; nothing about the output
changed. The one remaining array is unavoidable without changing results:
percentiles need every path on each date, and the seeded generator draws
path by path, so generating dates in chunks would give different numbers.

Student-t uses the same single buffer. Bootstrap fills it 1,000 paths at a
time, so its day indices never need a second full array; it peaks at about
121 MB (1.2 full arrays) at 10,000 × 1,260.

**Assumptions and limitations.**
- Daily returns are drawn independently, so there is no volatility
  clustering or regime change. The normal model also has no fat tails;
  Student-t and bootstrap add them, but real crashes can still be worse than
  the 5th percentile.
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
   with the target weights at the chosen rebalance frequency, daily by
   default (`portfolio_returns`).
3. Report realized `cumulative_return`, `max_drawdown` (negative) and
   `annualized_volatility` (sample std × √252). These come from the same
   metric functions the dashboard uses.

**Unavailable scenarios.** A result has `available=False`, a plain-language
`reason` and no metrics when:
- an asset's first actual price is more than one weekday after the window
  start (for example, it listed later), or
- its last actual price is more than one weekday before the window end, or
- fewer than 3 common price dates fall inside the window.

The reason names only the assets that fall short and the edge they miss,
for example `NEW history starts 2020-03-02, after the scenario start
2020-02-19` or `OLD has no price data`.

Weekends never count against coverage, and one missing weekday is allowed at
each edge for an exchange holiday.

**Inputs.** `prices` is a dated, sorted, unique DataFrame of positive
prices. NaN means "no observation", for example before an asset listed.
Fetch it with `fetch_price_history` so each asset keeps its own coverage;
prices from `fetch_prices` are cut to shared dates, so one late listing
makes every asset look short.
Invalid prices, weights or scenarios raise `ValueError`. Scenario dates are
stored as timezone-naive midnight timestamps, and timezone-aware price
indexes are matched by calendar date.

**Limitations.**
- Results are hypothetical, using today's weights and daily rebalancing.
- A dropped day is not a dropped return: the next return spans both trading
  days and still counts as one daily observation, so `n_returns` falls by one
  per dropped day. A two-day return has about twice the variance of a one-day
  return, so on average `annualized_volatility` is slightly overstated, not
  understated.
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

history = data.fetch_price_history(["SPY", "TLT"], start="2007-01-01", end="2023-01-01")
for result in analytics.run_stress_tests(history, [0.6, 0.4]):
    if result.available:
        print(result.scenario.name, result.cumulative_return, result.max_drawdown)
    else:
        print(result.scenario.name, "unavailable:", result.reason)

covid_tail = analytics.custom_scenario("2020-02-19", "2020-06-30", name="COVID and rebound")
print(analytics.stress_test(history, [0.6, 0.4], covid_tail))
```

Fetch from before the earliest scenario so coverage can be checked. With
`fetch_price_history`, a recently listed ticker makes only the older
scenarios it missed unavailable, and the reason names that ticker alone.

## What-if trades and custom shocks

Both tools are tabs next to **Simulated futures** and **Historical
scenarios**, and each runs only when you press its button.

### What-if trade (`trade_weights`, `compare_portfolios`)

Pick a holding to sell, a ticker to buy (one you hold or a new one), and an
amount as a percent of the whole portfolio, not of the holding sold.
**Simulate trade** shows the weights and metrics before and after, side by
side.

- `trade_weights(weights, sell, buy, amount)` moves `amount` (a fraction of
  total value, 0.10 = 10%) from `sell` to `buy`. A new ticker is added at
  the end, and a holding sold down to zero keeps a 0 weight. It raises
  `ValueError` when `sell` is not held, `buy` is blank or the same ticker, or
  `amount` is not in (0, weight of `sell`].
- `compare_portfolios(prices, before, after, risk_free_rate=0.0,
  rebalance="daily", cost_bps=0.0, confidence=0.95)` runs
  `analyze_portfolio` and one-day historical VaR and CVaR for both weight
  sets on the same prices. It returns a DataFrame indexed by
  `COMPARISON_METRICS` (annualized return and volatility, Sharpe, Sortino,
  max drawdown, VaR, CVaR, annual turnover) with `before`, `after`, and
  `change` (after − before) columns. A ticker missing from one weight set
  counts as 0.
- `trade_cost(amount, cost_bps)` is the one-time cost of the trade itself,
  `2 × amount × cost_bps / 10,000` of portfolio value (the sale plus the
  purchase), the same rule rebalancing uses. The dashboard shows it next to
  the table but leaves it out of the metrics.

Buying a ticker you do not hold downloads it for your analysis dates. Both
columns then use only the dates every ticker shares, so a recently listed
ticker can shorten the period; the caption gives the dates used. Both
columns follow your rebalancing and trading cost.

### Custom shocks (`shock_impact`)

Enter a move in percent for one or more of the proxies in `SHOCK_PROXIES`:

| Proxy | ETF |
|-------|-----|
| Market | SPY |
| Technology | XLK |
| Financials | XLF |
| Energy | XLE |
| Long-term bonds | TLT |
| Gold | GLD |

**Apply shocks** downloads the shocked ETFs for your analysis dates, and
`shock_impact(asset_returns, proxy_returns, weights, shocks)`:

1. regresses each holding's daily returns on the shocked proxies' daily
   returns by least squares with an intercept, over the dates both share
   (at least `MIN_SHOCK_OBS`, 60);
2. sets each holding's move to its betas times the shocks, capped at −100%
   because a long position cannot lose more than its value;
3. adds up weight × move to get the portfolio's move.

```
move_i = max(−1, Σ_f β_i,f · shock_f)        portfolio move = Σ_i w_i · move_i
```

It returns a `ShockImpact` with the portfolio move, a table per holding
(weight, move, contribution, R²), the betas, the shocks used, and the dates.
Proxies left at 0% are not in the regression, so a beta to technology also
picks up whatever moves with technology, such as the broad market; shock
several proxies together to separate them. Each shock must be above −100%,
and proxies that do not move or move in lockstep are rejected because their
effects cannot be told apart. The estimate is linear and instantaneous, uses
your target weights, and is not a prediction.

## File structure

```
app.py                    Streamlit dashboard
src/risklens/
  validation.py           Ticker, weight, risk-free rate, price, and date checks
  data.py                 Price download (yfinance): aligned prices, per-ticker history,
                          SPY benchmark, daily returns; Fama-French factors (Ken French
                          library) and sector/country labels (Yahoo profiles)
  holdings.py             Holdings CSV parsing; shares or dollar values to weights
  analytics/
    engine.py             analyze_portfolio and PortfolioMetrics
    metrics.py            Return-based metrics (volatility, Sharpe, Sortino, Calmar,
                          VaR/CVaR, drawdown, ...)
    value_at_risk.py      Normal and Cornish-Fisher VaR, rolling VaR, Kupiec backtest
    rolling.py            Dated rolling volatility, Sharpe, and drawdown
    volatility.py         EWMA and GARCH(1,1) volatility forecasts
    optimization.py       Long-only min-volatility and max-Sharpe weights (SciPy)
    benchmark.py          Portfolio vs. SPY growth, statistics, information ratio, capture
    concentration.py      Herfindahl index, effective holdings, correlation
    attribution.py        Fama-French factor regression; sector/country breakdown
    simulation.py         Seeded Monte Carlo wealth paths (simulate_portfolio):
                          normal, Student-t, or bootstrap daily returns
    stress.py             Historical stress windows (stress_test, custom_scenario)
    what_if.py            What-if trades: trade weights, trade cost, before/after metrics
    shocks.py             Custom shocks to proxy ETFs, passed to holdings through betas
tests/                    pytest suite (network-free); test_smoke.py,
                          test_tail_risk_ui.py, test_risk_ui.py,
                          test_holdings_ui.py, test_risk_metrics_ui.py,
                          test_risk_sources_ui.py, test_what_if_ui.py,
                          test_shocks_ui.py, test_volatility_ui.py, and
                          test_simulation_tails_ui.py
                          drive the dashboard with AppTest
benchmarks/               Reproducible benchmarks (simulation_memory.py: Monte
                          Carlo peak memory at 10,000 paths × 1,260 days)
pyproject.toml            Package metadata, dependencies, pytest and Ruff config
AGENTS.md                 Architecture, ownership, and coding rules
LICENSE                   MIT license
```

See [AGENTS.md](AGENTS.md) for architecture, ownership, and coding rules.
