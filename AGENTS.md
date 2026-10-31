# AGENTS.md — RiskLens Quant

Guide for every AI agent (Claude, Codex) and human working in this repo.

## Architecture

Single-process Python app. No separate backend, no database.

```
app.py (Streamlit UI)
   │  calls
   ▼
src/risklens/
   validation.py      user input → clean tickers / weights / dates (raises ValueError)
   data.py            tickers → price DataFrame (yfinance) → daily returns
   analytics/
     metrics.py       returns + weights → portfolio returns → risk metrics, VaR/CVaR
     engine.py        adjusted prices + weights → PortfolioMetrics
     benchmark.py     portfolio vs. SPY growth and statistics
     concentration.py HHI, effective holdings, correlation matrix
     rolling.py       daily returns → dated rolling volatility, Sharpe, drawdown
     optimization.py  adjusted prices → long-only min-vol / max-Sharpe weights, efficient frontier
     simulation.py    daily returns → seeded Monte Carlo wealth percentiles
     stress.py        prices + weights → historical stress-window results
```

Data flow: raw input → `validation` → `data.fetch_prices` → `data.to_returns`
→ `analytics.analyze_portfolio` (→ `portfolio_returns` → metric functions)
→ UI charts/tables.

Rules of the layering:
- `risklens` modules never import Streamlit or Plotly. They return plain
  Python / numpy / pandas values so they are testable without a UI.
- Only `data.py` touches the network.
- Validation happens at the boundary (`validation.py`) and again where a
  function would silently produce wrong numbers (e.g. `portfolio_returns`).
- Errors are raised with clear messages; the UI decides how to display them.

## Ownership

| Area | Owner |
|------|-------|
| `pyproject.toml`, `README.md`, `.gitignore`, `AGENTS.md` | Claude |
| `src/risklens/` (data, validation, risk analytics) | Claude |
| `app.py`, any `ui/` or chart/visualization modules | Codex |
| `tests/` | Codex |
| Lines marked `TODO(human)` | Human |

## Agent rules

1. **Claude owns financial logic and infrastructure.**
2. **Codex owns the Streamlit UI, visualization, and tests.**
3. **Every task leaves 10–15 meaningful Python lines for the human to type.**
   Mark the insertion point with `TODO(human)`, keep the surrounding code
   importable, and make the gap real logic (not boilerplate).
4. **Show, don't insert.** In the final response, show the exact code to
   type, explain each line simply, and name the file and insertion point.
   Never write those lines into the file yourself.
5. **Never overwrite another agent's files.** If you need a change in a file
   you don't own, describe it in your summary instead of editing it.
6. **Keep changes simple, accurate, and testable.**

## Coding standards

- Python ≥ 3.11, type hints on all public functions, docstrings that state
  units (daily vs. annualized, fraction vs. percent).
- Functions are pure where possible; do not mutate inputs.
- Named constants for financial conventions (`TRADING_DAYS_PER_YEAR = 252`).
- Returns are simple (arithmetic) daily returns expressed as fractions.
- VaR and drawdown sign conventions are documented in each function.
- Small modules (< 400 lines), small functions (< 50 lines).
- Raise `ValueError` for bad input, `DataFetchError` for download problems.
- Tests use pytest, live in `tests/`, and must not hit the network (mock
  `yfinance.download`).
