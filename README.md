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
  validation.py         Ticker and weight input checks
  data.py               Price download (yfinance) and returns
  risk.py               Portfolio risk metrics
tests/                  pytest suite
```

## Library usage

```python
from risklens import data, risk, validation

tickers = validation.validate_tickers("AAPL, msft, SPY")
weights = validation.validate_weights([0.4, 0.4, 0.2], len(tickers))
prices = data.fetch_prices(tickers, start="2023-01-01", end="2024-01-01")
port = risk.portfolio_returns(data.to_returns(prices), weights)
print(risk.annualized_volatility(port), risk.historical_var(port))
```

See [AGENTS.md](AGENTS.md) for architecture, ownership, and coding rules.
