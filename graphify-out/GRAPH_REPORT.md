# Graph Report - RiskLens  (2026-11-02)

## Corpus Check
- 49 files · ~117,068 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 889 nodes · 2726 edges · 34 communities (29 shown, 5 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 445 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `96d464f6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- custom_scenario
- pytest
- simulate_portfolio
- data.py
- analyze_portfolio
- efficient_frontier
- test_risk_ui.py
- pandas
- metrics.py
- risklens
- test_optimization.py
- pytest
- optimization.py
- test_metrics_regression.py
- OptimizationError
- submit
- EfficientFrontier
- test_stress_history_ui.py
- app.py
- stress_test
- test_stress.py
- test_simulation_memory.py
- analytics/__init__.py
- test_simulation.py
- RiskLens Quant
- min_volatility_portfolio
- test_stress_history.py
- test_simulation_regression.py
- simulation.py
- simulation_memory.py
- _parse_date
- test_stress_dropped_days.py
- test_invalid_tail_data_hides_risk_results

## God Nodes (most connected - your core abstractions)
1. `stress_test()` - 59 edges
2. `Analytics API` - 52 edges
3. `efficient_frontier()` - 50 edges
4. `simulate_portfolio()` - 50 edges
5. `five_assets()` - 46 edges
6. `analyze_portfolio()` - 33 edges
7. `min_volatility_portfolio()` - 31 edges
8. `custom_scenario()` - 29 edges
9. `click_button()` - 28 edges
10. `max_sharpe_portfolio()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Coding standards` --references--> `DataFetchError`  [INFERRED]
  AGENTS.md → src/risklens/data.py
- `Usage` --references--> `fetch_price_history()`  [INFERRED]
  README.md → src/risklens/data.py
- `Analytics API` --references--> `BenchmarkStatistics`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py

## Import Cycles
- None detected.

## Communities (34 total, 5 thin omitted)

### Community 0 - "custom_scenario"
Cohesion: 0.21
Nodes (14): custom_scenario(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_early_history_end_allows_at_most_one_missing_weekday(), test_holiday_monday_end_with_friday_last_price_is_available(), test_invalid_scenarios_are_rejected_at_construction(), test_late_listing_allows_at_most_one_missing_weekday(), test_non_scenario_argument_raises_value_error() (+6 more)

### Community 1 - "pytest"
Cohesion: 0.07
Nodes (27): _parse_date(), validate_date_range(), validate_price_history(), validate_risk_free_rate(), validate_tickers(), validate_weights(), test_matching_time_zones_are_accepted(), test_missing_or_nonsense_start_is_rejected() (+19 more)

### Community 2 - "simulate_portfolio"
Cohesion: 0.22
Nodes (19): simulate_portfolio(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility(), test_constant_history_is_deterministic(), test_every_path_starts_at_wealth_one_on_the_last_historical_date() (+11 more)

### Community 3 - "data.py"
Cohesion: 0.10
Nodes (28): _close_prices(), DataFetchError, _download_close(), fetch_benchmark_prices(), fetch_price_history(), fetch_prices(), dates(), fetch() (+20 more)

### Community 4 - "analyze_portfolio"
Cohesion: 0.18
Nodes (10): Architecture, analyze_portfolio(), PortfolioMetrics, to_returns(), validate_prices(), assert_same_metrics(), test_all_weight_on_one_asset_gives_that_assets_metrics(), test_price_level_of_an_asset_does_not_change_metrics() (+2 more)

### Community 5 - "efficient_frontier"
Cohesion: 0.14
Nodes (27): efficient_frontier(), EfficientFrontier, frontier_point_within_risk(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_estimates_inputs_and_solves_min_volatility_once(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_frontier_weights_are_long_only_and_metrics_match_engine() (+19 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (18): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_frontier_reuses_the_minimum_volatility_result(), test_frontier_solves_its_own_minimum_volatility_after_a_failure(), test_least_risky_current_portfolio_has_no_same_risk_point() (+10 more)

### Community 7 - "pandas"
Cohesion: 0.05
Nodes (55): _aligned_returns(), benchmark_statistics(), compare_to_benchmark(), correlation_matrix(), effective_holdings(), herfindahl_index(), series_from_returns(), test_constant_benchmark_returns_are_rejected() (+47 more)

### Community 8 - "metrics.py"
Cohesion: 0.06
Nodes (47): annualized_return(), _as_float_values(), _drifted_returns(), historical_cvar(), historical_var(), _rebalance_periods(), risk_contributions(), sharpe_ratio() (+39 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.11
Nodes (28): estimate_inputs(), max_sharpe_portfolio(), make_prices(), random_portfolios(), test_max_sharpe_is_at_least_every_frontier_point(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved() (+20 more)

### Community 12 - "pytest"
Cohesion: 0.09
Nodes (38): Rolling risk metrics, _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility() (+30 more)

### Community 13 - "optimization.py"
Cohesion: 0.11
Nodes (9): Portfolio optimization, _min_volatility(), OptimizedPortfolio, _portfolio(), _reused_min_volatility_return(), _solve(), SolverDiagnostics, _target_return_solve() (+1 more)

### Community 14 - "test_metrics_regression.py"
Cohesion: 0.13
Nodes (16): drawdown_series(), dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates(), dated() (+8 more)

### Community 15 - "OptimizationError"
Cohesion: 0.21
Nodes (7): OptimizationError, test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error(), test_solver_failure_raises_optimization_error()

### Community 16 - "submit"
Cohesion: 0.06
Nodes (20): chart_values(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results() (+12 more)

### Community 17 - "EfficientFrontier"
Cohesion: 0.33
Nodes (3): render_frontier(), render_optimization(), render_optimization_results()

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.10
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.17
Nodes (5): render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_tail_risk()

### Community 20 - "stress_test"
Cohesion: 0.17
Nodes (11): Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), Rebalancing, max_drawdown(), _coverage_gaps(), _naive_dates(), run_stress_tests(), stress_test() (+3 more)

### Community 21 - "test_stress.py"
Cohesion: 0.14
Nodes (15): prices(), test_every_short_asset_is_named_in_column_order(), test_exactly_three_common_prices_is_available(), test_reordering_assets_with_their_weights_changes_nothing(), test_single_asset_return_is_its_price_ratio(), test_asset_listed_after_window_start_is_unavailable(), test_custom_scenario_rejects_bad_dates(), test_custom_scenario_rejects_blank_name() (+7 more)

### Community 22 - "test_simulation_memory.py"
Cohesion: 0.16
Nodes (8): assert_identical(), copying_simulation(), returns(), test_largest_supported_run_matches_the_copying_implementation(), test_peak_memory_stays_near_one_path_buffer(), test_same_seed_matches_the_copying_implementation_exactly(), test_terminal_returns_survive_the_in_place_percentile_partition(), test_zero_volatility_history_matches_the_copying_implementation()

### Community 23 - "analytics/__init__.py"
Cohesion: 0.18
Nodes (5): render_stress_test(), BenchmarkStatistics, annualized_volatility(), cumulative_wealth(), portfolio_returns()

### Community 24 - "test_simulation.py"
Cohesion: 0.21
Nodes (11): history(), returns(), test_does_not_mutate_returns(), test_paths_start_at_one_on_last_date_and_move_forward(), test_percentiles_are_ordered_and_terminal_stats_agree(), test_rejects_bad_returns(), test_rejects_bad_settings(), test_same_seed_reproduces_and_new_seed_differs() (+3 more)

### Community 25 - "RiskLens Quant"
Cohesion: 0.12
Nodes (14): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR, Installation (+6 more)

### Community 26 - "min_volatility_portfolio"
Cohesion: 0.18
Nodes (8): min_volatility_portfolio(), assert_kkt(), redundant_assets(), test_first_frontier_point_holds_the_min_volatility_weights(), test_max_sharpe_satisfies_kkt_conditions(), test_min_volatility_satisfies_kkt_with_a_binding_long_only_bound(), test_rescaling_one_price_column_leaves_weights_unchanged(), test_min_volatility_weights_ignore_risk_free_rate()

### Community 27 - "test_stress_history.py"
Cohesion: 0.32
Nodes (10): history(), test_common_dates_hid_which_asset_listed_late(), test_custom_window_after_listing_is_available(), test_delisted_ticker_reports_the_scenario_end(), test_every_scenario_names_only_the_late_listing(), test_fully_covered_portfolio_matches_common_date_results(), test_missing_day_inside_window_is_dropped_not_reported(), test_recent_ipo_is_the_only_asset_blamed() (+2 more)

### Community 28 - "test_simulation_regression.py"
Cohesion: 0.26
Nodes (7): history(), noisy(), test_break_even_paths_are_not_counted_as_losses(), test_duplicate_dates_and_worse_than_total_loss_are_rejected(), test_friday_history_continues_on_the_next_consecutive_weekdays(), test_percentile_bands_match_lognormal_quantiles(), test_seed_above_the_32_bit_range_is_rejected()

### Community 29 - "simulation.py"
Cohesion: 0.15
Nodes (4): _estimate_parameters(), _future_dates(), MonteCarloResult, _validate_int()

### Community 30 - "simulation_memory.py"
Cohesion: 0.33
Nodes (3): benchmark_returns(), main(), measure()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 270 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `stress_test` to `custom_scenario`, `pytest`, `simulate_portfolio`, `data.py`, `analyze_portfolio`, `efficient_frontier`, `pandas`, `metrics.py`, `test_optimization.py`, `pytest`, `optimization.py`, `test_metrics_regression.py`, `OptimizationError`, `analytics/__init__.py`, `RiskLens Quant`, `min_volatility_portfolio`, `simulation.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 43 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `pytest` be split into smaller, more focused modules?**
  _Cohesion score 0.06802721088435375 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `simulate_portfolio` to `pandas`, `metrics.py`, `submit`, `app.py`, `stress_test`, `test_simulation_memory.py`, `analytics/__init__.py`, `test_simulation.py`, `RiskLens Quant`, `test_simulation_regression.py`, `simulation.py`, `simulation_memory.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Should `data.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09898242368177614 - nodes in this community are weakly interconnected._