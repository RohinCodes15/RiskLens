# Graph Report - RiskLens  (2026-11-01)

## Corpus Check
- 39 files · ~112,585 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 732 nodes · 2245 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 368 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e7dbe760`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- validation.py
- numpy
- data.py
- test_smoke.py
- efficient_frontier
- test_risk_ui.py
- pandas
- pytest
- risklens
- test_optimization.py
- pytest
- optimization.py
- test_metrics.py
- test_invalid_tail_data_hides_risk_results
- submit
- analyze_portfolio
- test_stress_history_ui.py
- OptimizationError
- to_returns
- render_optimization
- _solve

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 52 edges
2. `stress_test()` - 49 edges
3. `simulate_portfolio()` - 39 edges
4. `efficient_frontier()` - 34 edges
5. `five_assets()` - 32 edges
6. `analyze_portfolio()` - 29 edges
7. `custom_scenario()` - 26 edges
8. `min_volatility_portfolio()` - 24 edges
9. `to_returns()` - 24 edges
10. `click_button()` - 24 edges

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

## Communities (23 total, 5 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.09
Nodes (39): render_stress_test(), custom_scenario(), stress_test(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates(), test_early_history_end_allows_at_most_one_missing_weekday(), test_holiday_monday_end_with_friday_last_price_is_available() (+31 more)

### Community 1 - "validation.py"
Cohesion: 0.05
Nodes (31): render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_tail_risk(), _parse_date(), validate_date_range(), validate_price_history() (+23 more)

### Community 2 - "numpy"
Cohesion: 0.11
Nodes (32): _estimate_parameters(), simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility() (+24 more)

### Community 3 - "data.py"
Cohesion: 0.06
Nodes (43): Agent rules, AGENTS.md — RiskLens Quant, Architecture, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR (+35 more)

### Community 4 - "test_smoke.py"
Cohesion: 0.12
Nodes (6): chart_values(), test_analyze_matches_engine_and_drawdown(), test_initial_dashboard_has_inputs_and_no_fake_results(), test_simulation_controls_fan_and_persistence(), app_data(), test_confidence_switch_uses_api_and_actual_histogram()

### Community 5 - "efficient_frontier"
Cohesion: 0.19
Nodes (18): render_frontier(), efficient_frontier(), EfficientFrontier, frontier_point_within_risk(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_frontier_weights_are_long_only_and_metrics_match_engine() (+10 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.17
Nodes (16): analyzed_app(), make_prices(), prices(), select(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_least_risky_current_portfolio_has_no_same_risk_point(), test_negative_returns_keep_minimum_volatility_and_frontier() (+8 more)

### Community 7 - "pandas"
Cohesion: 0.08
Nodes (35): compare_to_benchmark(), correlation_matrix(), effective_holdings(), herfindahl_index(), _future_dates(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta() (+27 more)

### Community 8 - "pytest"
Cohesion: 0.05
Nodes (38): Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, PortfolioMetrics, annualized_return(), annualized_volatility() (+30 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.13
Nodes (22): max_sharpe_portfolio(), make_prices(), random_portfolios(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved(), test_infeasible_solver_output_raises_optimization_error(), test_invalid_prices_are_rejected() (+14 more)

### Community 12 - "pytest"
Cohesion: 0.07
Nodes (45): Rolling risk metrics, drawdown_series(), _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe() (+37 more)

### Community 13 - "optimization.py"
Cohesion: 0.14
Nodes (9): Portfolio optimization, min_volatility_portfolio(), OptimizedPortfolio, _portfolio(), SolverDiagnostics, _validate_points(), validate_risk_free_rate(), test_min_volatility_matches_two_asset_closed_form() (+1 more)

### Community 14 - "test_metrics.py"
Cohesion: 0.14
Nodes (21): historical_cvar(), historical_var(), tail_risk_summary(), _validate_confidence(), test_exactly_one_tail_observation_counts_as_sufficient(), test_non_numeric_confidence_raises_value_error(), test_numpy_and_python_floats_are_accepted(), test_summary_rejects_returns_with_nan() (+13 more)

### Community 16 - "submit"
Cohesion: 0.08
Nodes (15): click_button(), download(), prices(), submit(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results(), test_historical_scenarios_use_their_own_download_window() (+7 more)

### Community 17 - "analyze_portfolio"
Cohesion: 0.26
Nodes (7): analyze_portfolio(), prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation(), test_rejects_invalid_inputs()

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.12
Nodes (14): app(), history(), replay(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis(), test_every_late_listed_stock_is_named_with_its_own_start(), test_late_listing_names_only_the_stock_with_insufficient_history() (+6 more)

### Community 19 - "OptimizationError"
Cohesion: 0.21
Nodes (7): OptimizationError, test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error(), test_solver_failure_raises_optimization_error()

### Community 20 - "to_returns"
Cohesion: 0.28
Nodes (6): estimate_inputs(), to_returns(), validate_prices(), test_estimate_inputs_annualizes_mean_and_sample_covariance(), test_estimate_inputs_needs_more_returns_than_assets(), test_max_sharpe_matches_interior_tangency_closed_form()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 219 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `pytest` to `stress_test`, `validation.py`, `numpy`, `data.py`, `efficient_frontier`, `pandas`, `test_optimization.py`, `pytest`, `optimization.py`, `test_metrics.py`, `analyze_portfolio`, `OptimizationError`, `to_returns`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.0861952861952862 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `validation.py`, `data.py`, `test_smoke.py`, `pandas`, `pytest`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Should `validation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05017921146953405 - nodes in this community are weakly interconnected._