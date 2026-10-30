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

Some tests are expected to show as `xfail` or `skipped`. They cover code
marked `TODO(human)` that hasn't been written yet (for example
`validation.validate_date_range`), and `-ra` prints the reason for each one.

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
`correlation_matrix`, and `TRADING_DAYS_PER_YEAR`. Each function's docstring
gives its units and sign conventions.

Errors: `ValueError` for bad input, `risklens.data.DataFetchError` for
download problems.

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
tests/                    pytest suite (network-free)
pyproject.toml            Package metadata, dependencies, pytest and Ruff config
AGENTS.md                 Architecture, ownership, and coding rules
```

See [AGENTS.md](AGENTS.md) for architecture, ownership, and coding rules.
