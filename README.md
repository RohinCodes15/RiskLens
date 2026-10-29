# RiskLens Quant

A portfolio risk analyzer built with Python and Streamlit. Enter tickers and
weights, pull historical prices from Yahoo Finance, and see volatility,
Value at Risk, Sharpe ratio, and drawdown for the portfolio.

There is no separate backend: the Streamlit app calls the `risklens` package
directly.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
streamlit run app.py
pytest
```

## Layout

```
app.py                  Streamlit UI (Codex)
src/risklens/
  validation.py         Ticker, weight, risk-free rate, and price checks
  data.py               Price download (yfinance) and returns
  analytics/
    metrics.py          Return-based risk metrics (volatility, Sharpe, VaR, drawdown)
    engine.py           analyze_portfolio: adjusted prices + weights -> metrics
    benchmark.py        Portfolio vs. SPY growth from a common 1.0
    concentration.py    Herfindahl index, effective holdings, correlation
tests/                  pytest suite
```

## Library usage

```python
from risklens import analytics, data, validation

tickers = validation.validate_tickers("AAPL, msft, SPY")
weights = validation.validate_weights([0.4, 0.4, 0.2], len(tickers))
prices = data.fetch_prices(tickers, start="2023-01-01", end="2024-01-01")
result = analytics.analyze_portfolio(prices, weights, risk_free_rate=0.04)
print(result.annualized_volatility, result.sharpe_ratio, result.max_drawdown)
```

See [AGENTS.md](AGENTS.md) for architecture, ownership, and coding rules.
