# Graph Report - RiskLens  (2026-10-31)

## Corpus Check
- 37 files · ~24,931 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 662 nodes · 1996 edges · 19 communities (17 shown, 2 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 342 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `20c9a3de`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- stress.py
- numpy
- data.py
- test_smoke.py
- analytics/__init__.py
- test_risk_ui.py
- pandas
- pytest
- risklens
- test_optimization.py
- test_rolling.py
- app.py
- analyze_portfolio
- test_tail_risk_ui.py
- DataFrame
- test_stress_unavailable_preserves_dashboard
- chart_spec

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 50 edges
2. `simulate_portfolio()` - 39 edges
3. `stress_test()` - 38 edges
4. `efficient_frontier()` - 33 edges
5. `five_assets()` - 32 edges
6. `analyze_portfolio()` - 29 edges
7. `custom_scenario()` - 24 edges
8. `min_volatility_portfolio()` - 23 edges
9. `max_sharpe_portfolio()` - 23 edges
10. `to_returns()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Analytics API` --references--> `compare_to_benchmark()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py
- `Analytics API` --references--> `benchmark_statistics()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py
- `Analytics API` --references--> `correlation_matrix()`  [INFERRED]
  README.md → src/risklens/analytics/concentration.py

## Import Cycles
- None detected.

## Communities (19 total, 2 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.07
Nodes (35): _coverage_gaps(), custom_scenario(), _naive_dates(), _parse_date(), stress_test(), StressScenario, _validate_price_history(), _weekdays_between() (+27 more)

### Community 1 - "stress.py"
Cohesion: 0.06
Nodes (25): _validate_points(), to_returns(), _parse_date(), validate_date_range(), validate_prices(), validate_tickers(), validate_weights(), test_matching_time_zones_are_accepted() (+17 more)

### Community 2 - "numpy"
Cohesion: 0.12
Nodes (31): _estimate_parameters(), simulate_portfolio(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility(), test_constant_history_is_deterministic() (+23 more)

### Community 3 - "data.py"
Cohesion: 0.06
Nodes (33): Agent rules, AGENTS.md — RiskLens Quant, Architecture, Coding standards, Ownership, render_stress_test(), Features, File structure (+25 more)

### Community 4 - "test_smoke.py"
Cohesion: 0.12
Nodes (9): chart_values(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_initial_dashboard_has_inputs_and_no_fake_results(), test_new_analysis_resets_both_scenario_tools(), test_simulation_controls_fan_and_persistence() (+1 more)

### Community 5 - "analytics/__init__.py"
Cohesion: 0.08
Nodes (27): Analytics API, Rolling risk metrics, BenchmarkStatistics, effective_holdings(), herfindahl_index(), PortfolioMetrics, max_drawdown(), SolverDiagnostics (+19 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.20
Nodes (14): analyzed_app(), make_prices(), prices(), select(), test_constant_prices_show_attribution_unavailable(), test_least_risky_current_portfolio_has_no_same_risk_point(), test_optimization_table_and_frontier_match_the_api(), test_optimization_waits_for_the_button() (+6 more)

### Community 7 - "pandas"
Cohesion: 0.08
Nodes (31): _aligned_returns(), benchmark_statistics(), compare_to_benchmark(), correlation_matrix(), _future_dates(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta() (+23 more)

### Community 8 - "pytest"
Cohesion: 0.06
Nodes (45): Historical stress testing (`stress_test`, `run_stress_tests`), annualized_return(), annualized_volatility(), _as_float_values(), cumulative_wealth(), historical_cvar(), historical_var(), portfolio_returns() (+37 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.05
Nodes (60): render_frontier(), render_optimization(), Portfolio optimization, efficient_frontier(), EfficientFrontier, estimate_inputs(), frontier_point_within_risk(), max_sharpe_portfolio() (+52 more)

### Community 12 - "test_rolling.py"
Cohesion: 0.11
Nodes (33): drawdown_series(), dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates(), dated() (+25 more)

### Community 13 - "app.py"
Cohesion: 0.17
Nodes (5): render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_tail_risk()

### Community 14 - "analyze_portfolio"
Cohesion: 0.26
Nodes (7): analyze_portfolio(), prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation(), test_rejects_invalid_inputs()

### Community 15 - "test_tail_risk_ui.py"
Cohesion: 0.17
Nodes (3): app_data(), test_invalid_tail_data_hides_risk_results(), test_small_sample_warning_and_zero_returns()

### Community 16 - "DataFrame"
Cohesion: 0.20
Nodes (4): download(), prices(), test_single_stock_shows_full_concentration_without_heatmap(), test_spy_comparison_shows_chart_and_ending_returns()

### Community 17 - "test_stress_unavailable_preserves_dashboard"
Cohesion: 0.20
Nodes (4): test_failed_analysis_clears_previous_results(), test_invalid_inputs_do_not_download(), test_simulation_failure_clears_stale_chart_and_persists(), test_stress_unavailable_preserves_dashboard()

### Community 18 - "chart_spec"
Cohesion: 0.29
Nodes (3): chart_spec(), test_historical_scenarios_use_their_own_download_window(), test_confidence_switch_uses_api_and_actual_histogram()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 199 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `analytics/__init__.py` to `stress_test`, `stress.py`, `numpy`, `data.py`, `pandas`, `pytest`, `test_optimization.py`, `test_rolling.py`, `analyze_portfolio`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.07199032062915911 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `data.py`, `test_smoke.py`, `analytics/__init__.py`, `pandas`, `pytest`, `app.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `simulate_portfolio()` (e.g. with `Analytics API` and `Monte Carlo (`simulate_portfolio`)`) actually correct?**
  _`simulate_portfolio()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `stress.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05901639344262295 - nodes in this community are weakly interconnected._