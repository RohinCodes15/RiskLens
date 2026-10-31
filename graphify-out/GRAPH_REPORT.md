# Graph Report - RiskLens  (2026-10-30)

## Corpus Check
- 29 files · ~16,004 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 453 nodes · 1293 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 174 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f3df91e9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- validation.py
- numpy
- data.py
- test_smoke.py
- metrics.py
- analytics/__init__.py
- pandas
- pytest
- risklens

## God Nodes (most connected - your core abstractions)
1. `simulate_portfolio()` - 39 edges
2. `stress_test()` - 38 edges
3. `custom_scenario()` - 24 edges
4. `analyze_portfolio()` - 23 edges
5. `portfolio_returns()` - 21 edges
6. `Analytics API` - 21 edges
7. `compare_to_benchmark()` - 18 edges
8. `annualized_volatility()` - 18 edges
9. `fetch_prices()` - 18 edges
10. `historical_var()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Analytics API` --references--> `compare_to_benchmark()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py
- `Architecture` --references--> `analyze_portfolio()`  [INFERRED]
  AGENTS.md → src/risklens/analytics/engine.py
- `Architecture` --references--> `portfolio_returns()`  [INFERRED]
  AGENTS.md → src/risklens/analytics/metrics.py
- `Analytics API` --references--> `portfolio_returns()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py

## Import Cycles
- None detected.

## Communities (11 total, 2 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.07
Nodes (37): Historical stress testing (`stress_test`, `run_stress_tests`), _coverage_gaps(), custom_scenario(), _naive_dates(), _parse_date(), run_stress_tests(), stress_test(), StressResult (+29 more)

### Community 1 - "validation.py"
Cohesion: 0.06
Nodes (26): render_simulation(), render_stress_result(), _parse_date(), validate_date_range(), validate_prices(), validate_risk_free_rate(), validate_tickers(), validate_weights() (+18 more)

### Community 2 - "numpy"
Cohesion: 0.09
Nodes (34): _estimate_parameters(), _future_dates(), MonteCarloResult, simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error() (+26 more)

### Community 3 - "data.py"
Cohesion: 0.06
Nodes (32): Agent rules, AGENTS.md — RiskLens Quant, Architecture, Coding standards, Ownership, Features, File structure, Installation (+24 more)

### Community 4 - "test_smoke.py"
Cohesion: 0.07
Nodes (20): chart_spec(), chart_values(), click_button(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe() (+12 more)

### Community 5 - "metrics.py"
Cohesion: 0.08
Nodes (26): render_stress_test(), annualized_return(), annualized_volatility(), _as_float_values(), cumulative_wealth(), historical_var(), portfolio_returns(), risk_contributions() (+18 more)

### Community 6 - "analytics/__init__.py"
Cohesion: 0.08
Nodes (26): Analytics API, correlation_matrix(), effective_holdings(), herfindahl_index(), analyze_portfolio(), PortfolioMetrics, drawdown_series(), max_drawdown() (+18 more)

### Community 7 - "pandas"
Cohesion: 0.12
Nodes (23): _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, compare_to_benchmark(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates() (+15 more)

### Community 8 - "pytest"
Cohesion: 0.16
Nodes (20): historical_cvar(), prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation(), test_rejects_invalid_inputs(), series() (+12 more)

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 143 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `simulate_portfolio()` connect `numpy` to `validation.py`, `data.py`, `test_smoke.py`, `analytics/__init__.py`, `pandas`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `simulate_portfolio()` (e.g. with `Analytics API` and `Monte Carlo (`simulate_portfolio`)`) actually correct?**
  _`simulate_portfolio()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.06994047619047619 - nodes in this community are weakly interconnected._
- **Why does `Analytics API` connect `analytics/__init__.py` to `stress_test`, `numpy`, `data.py`, `metrics.py`, `pandas`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `stress_test()` (e.g. with `render_stress_test()` and `Analytics API`) actually correct?**
  _`stress_test()` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Should `validation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05649350649350649 - nodes in this community are weakly interconnected._