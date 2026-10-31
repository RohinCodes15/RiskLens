# Graph Report - RiskLens  (2026-10-31)

## Corpus Check
- 36 files · ~23,028 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 625 nodes · 1859 edges · 15 communities (13 shown, 2 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 314 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `25fb17a7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- validation.py
- numpy
- data.py
- test_smoke.py
- analytics/__init__.py
- test_concentration.py
- pandas
- pytest
- risklens
- test_optimization.py
- test_rolling.py
- app.py
- test_drawdown.py

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 49 edges
2. `simulate_portfolio()` - 39 edges
3. `stress_test()` - 38 edges
4. `analyze_portfolio()` - 27 edges
5. `five_assets()` - 26 edges
6. `efficient_frontier()` - 25 edges
7. `custom_scenario()` - 24 edges
8. `estimate_inputs()` - 22 edges
9. `portfolio_returns()` - 21 edges
10. `min_volatility_portfolio()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Analytics API` --references--> `compare_to_benchmark()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py
- `Analytics API` --references--> `herfindahl_index()`  [INFERRED]
  README.md → src/risklens/analytics/concentration.py
- `Analytics API` --references--> `effective_holdings()`  [INFERRED]
  README.md → src/risklens/analytics/concentration.py

## Import Cycles
- None detected.

## Communities (15 total, 2 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.09
Nodes (31): render_stress_test(), custom_scenario(), _parse_date(), stress_test(), _weekdays_between(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates() (+23 more)

### Community 1 - "validation.py"
Cohesion: 0.11
Nodes (15): validate_prices(), validate_tickers(), validate_weights(), prices(), test_date_range_rejects_bad_input(), test_prices_honour_min_rows(), test_prices_reject_bad_input(), test_prices_return_float_copy_without_mutating_input() (+7 more)

### Community 2 - "numpy"
Cohesion: 0.11
Nodes (32): _estimate_parameters(), simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility() (+24 more)

### Community 3 - "data.py"
Cohesion: 0.06
Nodes (31): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR, Installation (+23 more)

### Community 4 - "test_smoke.py"
Cohesion: 0.05
Nodes (24): chart_spec(), chart_values(), click_button(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe() (+16 more)

### Community 5 - "analytics/__init__.py"
Cohesion: 0.06
Nodes (31): Architecture, Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), Rolling risk metrics, _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, analyze_portfolio() (+23 more)

### Community 6 - "test_concentration.py"
Cohesion: 0.14
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 7 - "pandas"
Cohesion: 0.09
Nodes (28): compare_to_benchmark(), _future_dates(), _parse_date(), validate_date_range(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates() (+20 more)

### Community 8 - "pytest"
Cohesion: 0.08
Nodes (39): historical_cvar(), historical_var(), tail_risk_summary(), _validate_confidence(), prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown() (+31 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.06
Nodes (53): Portfolio optimization, efficient_frontier(), EfficientFrontier, estimate_inputs(), max_sharpe_portfolio(), min_volatility_portfolio(), OptimizationError, OptimizedPortfolio (+45 more)

### Community 12 - "test_rolling.py"
Cohesion: 0.09
Nodes (37): _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility(), _validate_window() (+29 more)

### Community 13 - "app.py"
Cohesion: 0.21
Nodes (3): render_simulation(), render_stress_result(), render_tail_risk()

### Community 14 - "test_drawdown.py"
Cohesion: 0.29
Nodes (6): dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 190 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `analytics/__init__.py` to `stress_test`, `validation.py`, `numpy`, `data.py`, `test_concentration.py`, `pandas`, `pytest`, `test_optimization.py`, `test_rolling.py`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 48 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.08776595744680851 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `data.py`, `test_smoke.py`, `analytics/__init__.py`, `pandas`, `app.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `simulate_portfolio()` (e.g. with `Analytics API` and `Monte Carlo (`simulate_portfolio`)`) actually correct?**
  _`simulate_portfolio()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `validation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11375661375661375 - nodes in this community are weakly interconnected._