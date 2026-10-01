# Graph Report - RiskLens  (2026-11-02)

## Corpus Check
- 56 files · ~123,490 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 1066 nodes · 3266 edges · 43 communities (39 shown, 4 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 520 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5ccd67d4`
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
- test_concentration.py
- historical_cvar
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
- portfolio_returns
- min_volatility_portfolio
- test_stress_history.py
- test_simulation_regression.py
- simulation.py
- simulation_memory.py
- test_rebalance_ui.py
- test_stress_dropped_days.py
- test_invalid_tail_data_hides_risk_results
- pandas
- test_holdings.py
- pytest
- numpy
- test_holdings_ui.py
- analytics/__init__.py
- test_tail_risk_audit.py
- test_metrics.py
- test_engine_regression.py

## God Nodes (most connected - your core abstractions)
1. `stress_test()` - 63 edges
2. `Analytics API` - 56 edges
3. `efficient_frontier()` - 50 edges
4. `simulate_portfolio()` - 50 edges
5. `portfolio_returns()` - 49 edges
6. `analyze_portfolio()` - 48 edges
7. `five_assets()` - 46 edges
8. `custom_scenario()` - 33 edges
9. `min_volatility_portfolio()` - 31 edges
10. `to_returns()` - 31 edges

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

## Communities (43 total, 4 thin omitted)

### Community 0 - "custom_scenario"
Cohesion: 0.21
Nodes (14): custom_scenario(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates(), test_early_history_end_allows_at_most_one_missing_weekday(), test_holiday_monday_end_with_friday_last_price_is_available(), test_invalid_scenarios_are_rejected_at_construction(), test_late_listing_allows_at_most_one_missing_weekday() (+6 more)

### Community 1 - "pytest"
Cohesion: 0.06
Nodes (31): _parse_date(), validate_cost_bps(), validate_date_range(), validate_price_history(), validate_prices(), validate_risk_free_rate(), validate_tickers(), validate_weights() (+23 more)

### Community 2 - "simulate_portfolio"
Cohesion: 0.22
Nodes (19): simulate_portfolio(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility(), test_constant_history_is_deterministic(), test_every_path_starts_at_wealth_one_on_the_last_historical_date() (+11 more)

### Community 3 - "data.py"
Cohesion: 0.10
Nodes (28): _close_prices(), DataFetchError, _download_close(), fetch_benchmark_prices(), fetch_price_history(), fetch_prices(), dates(), fetch() (+20 more)

### Community 4 - "analyze_portfolio"
Cohesion: 0.12
Nodes (22): Architecture, analyze_portfolio(), to_returns(), prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation() (+14 more)

### Community 5 - "efficient_frontier"
Cohesion: 0.16
Nodes (26): efficient_frontier(), frontier_point_within_risk(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_estimates_inputs_and_solves_min_volatility_once(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_frontier_weights_are_long_only_and_metrics_match_engine(), test_invalid_point_counts_are_rejected() (+18 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (18): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_frontier_reuses_the_minimum_volatility_result(), test_frontier_solves_its_own_minimum_volatility_after_a_failure(), test_least_risky_current_portfolio_has_no_same_risk_point() (+10 more)

### Community 7 - "test_concentration.py"
Cohesion: 0.16
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 8 - "historical_cvar"
Cohesion: 0.20
Nodes (16): historical_cvar(), tail_risk_summary(), _validate_confidence(), series(), test_cvar_averages_returns_at_or_below_var_threshold(), test_cvar_does_not_mutate_input(), test_cvar_is_negative_when_every_day_gains(), test_cvar_is_never_below_var() (+8 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.11
Nodes (29): estimate_inputs(), max_sharpe_portfolio(), make_prices(), random_portfolios(), test_max_sharpe_is_at_least_every_frontier_point(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved() (+21 more)

### Community 12 - "pytest"
Cohesion: 0.09
Nodes (38): Rolling risk metrics, _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility() (+30 more)

### Community 13 - "optimization.py"
Cohesion: 0.13
Nodes (7): _min_volatility(), OptimizedPortfolio, _portfolio(), _reused_min_volatility_return(), _solve(), _target_return_solve(), _validate_points()

### Community 14 - "test_metrics_regression.py"
Cohesion: 0.24
Nodes (9): dated(), noisy(), test_portfolio_return_is_weighted_but_volatility_is_diversified(), test_risk_contributions_ignore_the_scale_of_returns(), test_sharpe_ratio_ignores_leverage_at_a_zero_risk_free_rate(), test_tail_risk_ignores_the_order_of_returns(), test_tail_risk_rises_with_confidence(), test_tail_risk_scales_with_exposure() (+1 more)

### Community 15 - "OptimizationError"
Cohesion: 0.21
Nodes (7): Portfolio optimization, OptimizationError, test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_solver_failure_raises_optimization_error()

### Community 16 - "submit"
Cohesion: 0.06
Nodes (20): chart_values(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results() (+12 more)

### Community 17 - "EfficientFrontier"
Cohesion: 0.25
Nodes (4): render_frontier(), render_optimization(), render_optimization_results(), EfficientFrontier

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.10
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.12
Nodes (9): cost_text(), dollar_change(), holding_inputs(), render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_stress_test() (+1 more)

### Community 20 - "stress_test"
Cohesion: 0.13
Nodes (7): _coverage_gaps(), _naive_dates(), _parse_date(), StressScenario, _weekdays_between(), _window(), test_scenario_dates_are_normalized_at_construction()

### Community 21 - "test_stress.py"
Cohesion: 0.16
Nodes (17): stress_test(), prices(), test_drawdown_is_peak_to_trough_inside_the_window(), test_every_short_asset_is_named_in_column_order(), test_exactly_three_common_prices_is_available(), test_reordering_assets_with_their_weights_changes_nothing(), test_single_asset_return_is_its_price_ratio(), test_asset_listed_after_window_start_is_unavailable() (+9 more)

### Community 22 - "test_simulation_memory.py"
Cohesion: 0.14
Nodes (9): MonteCarloResult, assert_identical(), copying_simulation(), returns(), test_largest_supported_run_matches_the_copying_implementation(), test_peak_memory_stays_near_one_path_buffer(), test_same_seed_matches_the_copying_implementation_exactly(), test_terminal_returns_survive_the_in_place_percentile_partition() (+1 more)

### Community 23 - "analytics/__init__.py"
Cohesion: 0.29
Nodes (5): Historical stress testing (`stress_test`, `run_stress_tests`), Rebalancing and trading costs, run_stress_tests(), StressResult, test_run_stress_tests_keeps_documented_scenarios_in_order()

### Community 24 - "test_simulation.py"
Cohesion: 0.21
Nodes (11): history(), returns(), test_does_not_mutate_returns(), test_paths_start_at_one_on_last_date_and_move_forward(), test_percentiles_are_ordered_and_terminal_stats_agree(), test_rejects_bad_returns(), test_rejects_bad_settings(), test_same_seed_reproduces_and_new_seed_differs() (+3 more)

### Community 25 - "portfolio_returns"
Cohesion: 0.06
Nodes (41): _as_float_values(), _drifted_returns(), _portfolio_inputs(), portfolio_returns(), _rebalance_periods(), rebalance_turnover(), _turnover(), test_portfolio_returns_weights_each_day() (+33 more)

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
Cohesion: 0.18
Nodes (3): _estimate_parameters(), _future_dates(), _validate_int()

### Community 30 - "simulation_memory.py"
Cohesion: 0.33
Nodes (3): benchmark_returns(), main(), measure()

### Community 31 - "test_rebalance_ui.py"
Cohesion: 0.17
Nodes (13): analyze(), card_values(), download(), prices(), spy(), test_controls_default_to_daily_rebalancing_without_costs(), test_daily_cost_free_optimization_has_no_baseline_note(), test_default_analysis_passes_daily_and_zero_cost() (+5 more)

### Community 34 - "pandas"
Cohesion: 0.09
Nodes (27): _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, compare_to_benchmark(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates() (+19 more)

### Community 35 - "test_holdings.py"
Cohesion: 0.06
Nodes (32): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR, Holdings input (+24 more)

### Community 36 - "pytest"
Cohesion: 0.23
Nodes (9): risk_contributions(), test_hedging_asset_has_negative_risk_contribution(), test_metrics_reject_bad_returns(), test_portfolio_returns_rejects_bad_returns(), test_risk_contributions_match_euler_decomposition(), test_risk_contributions_reject_bad_returns(), test_risk_contributions_reject_non_dataframe_returns(), test_risk_contributions_sum_to_one_and_follow_columns() (+1 more)

### Community 37 - "numpy"
Cohesion: 0.33
Nodes (5): shocked(), test_max_drawdown_holds_the_drop_for_exactly_one_window(), test_rolling_sharpe_ignores_leverage_at_a_zero_risk_free_rate(), test_volatility_is_raised_only_while_the_shock_is_in_the_window(), windows_containing_shock()

### Community 38 - "test_holdings_ui.py"
Cohesion: 0.17
Nodes (20): analyze(), captions(), download(), enter_holdings(), prices(), test_bad_csv_lists_its_rows_and_blocks_analysis(), test_cards_have_no_dollar_amounts_without_a_portfolio_value(), test_csv_import_replaces_the_manual_inputs() (+12 more)

### Community 39 - "analytics/__init__.py"
Cohesion: 0.15
Nodes (13): Analytics API, PortfolioMetrics, cumulative_wealth(), drawdown_series(), max_drawdown(), SolverDiagnostics, dated(), test_does_not_mutate_input() (+5 more)

### Community 40 - "test_tail_risk_audit.py"
Cohesion: 0.33
Nodes (4): test_exactly_one_tail_observation_counts_as_sufficient(), test_non_numeric_confidence_raises_value_error(), test_numpy_and_python_floats_are_accepted(), test_summary_rejects_returns_with_nan()

### Community 41 - "test_metrics.py"
Cohesion: 0.19
Nodes (14): annualized_return(), annualized_volatility(), historical_var(), sharpe_ratio(), _validate_dated_returns(), _validate_returns(), series(), test_annualized_return_and_volatility_use_252_days() (+6 more)

### Community 42 - "test_engine_regression.py"
Cohesion: 0.43
Nodes (5): assert_same_metrics(), test_all_weight_on_one_asset_gives_that_assets_metrics(), test_price_level_of_an_asset_does_not_change_metrics(), test_splitting_an_asset_across_identical_columns_changes_nothing(), two_assets()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 311 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `analytics/__init__.py` to `custom_scenario`, `pytest`, `simulate_portfolio`, `data.py`, `analyze_portfolio`, `efficient_frontier`, `test_concentration.py`, `historical_cvar`, `test_optimization.py`, `pytest`, `optimization.py`, `OptimizationError`, `EfficientFrontier`, `stress_test`, `test_stress.py`, `test_simulation_memory.py`, `analytics/__init__.py`, `portfolio_returns`, `min_volatility_portfolio`, `pandas`, `test_holdings.py`, `pytest`, `test_metrics.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 47 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `pytest` be split into smaller, more focused modules?**
  _Cohesion score 0.05750658472344162 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `simulate_portfolio` to `pandas`, `test_holdings.py`, `numpy`, `analytics/__init__.py`, `submit`, `app.py`, `test_simulation_memory.py`, `test_simulation.py`, `test_simulation_regression.py`, `simulation.py`, `simulation_memory.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Should `data.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10253699788583509 - nodes in this community are weakly interconnected._