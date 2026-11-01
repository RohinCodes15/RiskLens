# Graph Report - RiskLens  (2026-11-01)

## Corpus Check
- 38 files · ~111,589 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 698 nodes · 2138 edges · 22 communities (19 shown, 3 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 362 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d4674470`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- stress.py
- numpy
- data.py
- test_smoke.py
- test_concentration.py
- test_risk_ui.py
- pandas
- pytest
- risklens
- test_optimization.py
- pytest
- efficient_frontier
- historical_cvar
- test_invalid_tail_data_hides_risk_results
- submit
- RiskLens Quant
- min_volatility_portfolio
- optimization.py
- OptimizationError
- render_frontier

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 52 edges
2. `stress_test()` - 46 edges
3. `simulate_portfolio()` - 39 edges
4. `efficient_frontier()` - 34 edges
5. `five_assets()` - 32 edges
6. `analyze_portfolio()` - 29 edges
7. `custom_scenario()` - 25 edges
8. `min_volatility_portfolio()` - 24 edges
9. `max_sharpe_portfolio()` - 23 edges
10. `to_returns()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Coding standards` --references--> `DataFetchError`  [INFERRED]
  AGENTS.md → src/risklens/data.py
- `Usage` --references--> `fetch_price_history()`  [INFERRED]
  README.md → src/risklens/data.py
- `Analytics API` --references--> `compare_to_benchmark()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py

## Import Cycles
- None detected.

## Communities (22 total, 3 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.06
Nodes (44): _coverage_gaps(), custom_scenario(), _naive_dates(), _parse_date(), stress_test(), StressScenario, _weekdays_between(), _window() (+36 more)

### Community 1 - "stress.py"
Cohesion: 0.05
Nodes (31): render_rolling(), render_simulation(), render_stress_result(), render_tail_risk(), _parse_date(), validate_date_range(), validate_price_history(), validate_prices() (+23 more)

### Community 2 - "numpy"
Cohesion: 0.11
Nodes (32): _estimate_parameters(), simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility() (+24 more)

### Community 3 - "data.py"
Cohesion: 0.10
Nodes (28): _close_prices(), DataFetchError, _download_close(), fetch_benchmark_prices(), fetch_price_history(), fetch_prices(), dates(), fetch() (+20 more)

### Community 4 - "test_smoke.py"
Cohesion: 0.12
Nodes (6): chart_values(), test_analyze_matches_engine_and_drawdown(), test_initial_dashboard_has_inputs_and_no_fake_results(), test_simulation_controls_fan_and_persistence(), app_data(), test_confidence_switch_uses_api_and_actual_histogram()

### Community 5 - "test_concentration.py"
Cohesion: 0.14
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (17): analyzed_app(), make_prices(), prices(), select(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_least_risky_current_portfolio_has_no_same_risk_point(), test_negative_returns_keep_minimum_volatility_and_frontier() (+9 more)

### Community 7 - "pandas"
Cohesion: 0.09
Nodes (26): _aligned_returns(), benchmark_statistics(), compare_to_benchmark(), _future_dates(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates() (+18 more)

### Community 8 - "pytest"
Cohesion: 0.05
Nodes (47): Architecture, render_risk_attribution(), render_stress_test(), Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), Rolling risk metrics, BenchmarkStatistics, analyze_portfolio() (+39 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.12
Nodes (23): max_sharpe_portfolio(), make_prices(), random_portfolios(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved(), test_infeasible_solver_output_raises_optimization_error(), test_invalid_prices_are_rejected(), test_invalid_risk_free_rate_is_rejected() (+15 more)

### Community 12 - "pytest"
Cohesion: 0.08
Nodes (43): _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility(), _validate_window() (+35 more)

### Community 13 - "efficient_frontier"
Cohesion: 0.21
Nodes (17): efficient_frontier(), EfficientFrontier, frontier_point_within_risk(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_frontier_weights_are_long_only_and_metrics_match_engine(), test_invalid_point_counts_are_rejected() (+9 more)

### Community 14 - "historical_cvar"
Cohesion: 0.25
Nodes (14): historical_cvar(), series(), test_cvar_averages_returns_at_or_below_var_threshold(), test_cvar_does_not_mutate_input(), test_cvar_is_negative_when_every_day_gains(), test_cvar_is_never_below_var(), test_cvar_rejects_bad_confidence(), test_cvar_rejects_bad_returns() (+6 more)

### Community 16 - "submit"
Cohesion: 0.08
Nodes (14): download(), prices(), submit(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results(), test_historical_scenarios_use_their_own_download_window(), test_invalid_inputs_do_not_download() (+6 more)

### Community 17 - "RiskLens Quant"
Cohesion: 0.12
Nodes (14): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR, Installation (+6 more)

### Community 18 - "min_volatility_portfolio"
Cohesion: 0.17
Nodes (10): Portfolio optimization, estimate_inputs(), min_volatility_portfolio(), OptimizedPortfolio, _portfolio(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_estimate_inputs_annualizes_mean_and_sample_covariance(), test_estimate_inputs_needs_more_returns_than_assets() (+2 more)

### Community 19 - "optimization.py"
Cohesion: 0.16
Nodes (4): _solve(), SolverDiagnostics, _target_return_solve(), _validate_points()

### Community 20 - "OptimizationError"
Cohesion: 0.31
Nodes (6): OptimizationError, test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error()

### Community 21 - "render_frontier"
Cohesion: 0.33
Nodes (3): render_frontier(), render_optimization(), render_optimization_results()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 204 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `pytest` to `stress_test`, `stress.py`, `numpy`, `data.py`, `test_concentration.py`, `pandas`, `test_optimization.py`, `pytest`, `efficient_frontier`, `historical_cvar`, `RiskLens Quant`, `min_volatility_portfolio`, `optimization.py`, `OptimizationError`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.06335403726708075 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `stress.py`, `test_smoke.py`, `pandas`, `pytest`, `RiskLens Quant`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Should `stress.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051715309779825906 - nodes in this community are weakly interconnected._