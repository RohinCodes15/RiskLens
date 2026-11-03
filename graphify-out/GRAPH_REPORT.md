# Graph Report - RiskLens  (2026-11-03)

## Corpus Check
- 71 files · ~52,541 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 1380 nodes · 4244 edges · 54 communities (49 shown, 5 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 659 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- test_what_if.py
- pytest
- simulate_portfolio
- test_data.py
- analyze_portfolio
- efficient_frontier
- test_risk_ui.py
- test_concentration.py
- historical_cvar
- risklens
- test_optimization.py
- test_rolling.py
- optimization.py
- test_metrics_regression.py
- OptimizationError
- test_smoke.py
- DataFetchError
- test_stress_history_ui.py
- app.py
- _coverage_gaps
- stress_test
- test_simulation_memory.py
- shock_impact
- test_simulation.py
- portfolio_returns
- min_volatility_portfolio
- test_what_if_ui.py
- test_simulation_regression.py
- _estimate_parameters
- simulation_memory.py
- test_rebalance_ui.py
- validate_date_range
- test_invalid_tail_data_hides_risk_results
- pandas
- test_holdings.py
- test_shocks_ui.py
- numpy
- test_holdings_ui.py
- factor_exposure
- benchmark_statistics
- historical_var
- value_at_risk.py
- data.py
- test_risk_metrics_ui.py
- test_value_at_risk.py
- sortino_ratio
- render_risk_sources
- test_benchmark_regression.py
- render_var_backtest
- test_benchmark_audit.py
- render_frontier
- analytics/__init__.py
- _active_shocks

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 72 edges
2. `stress_test()` - 63 edges
3. `analyze_portfolio()` - 61 edges
4. `efficient_frontier()` - 50 edges
5. `simulate_portfolio()` - 50 edges
6. `portfolio_returns()` - 49 edges
7. `five_assets()` - 46 edges
8. `to_returns()` - 34 edges
9. `custom_scenario()` - 33 edges
10. `min_volatility_portfolio()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Coding standards` --references--> `DataFetchError`  [INFERRED]
  AGENTS.md → src/risklens/data.py
- `Usage` --references--> `fetch_price_history()`  [INFERRED]
  README.md → src/risklens/data.py
- `Factor and sector exposure` --references--> `FactorExposure`  [INFERRED]
  README.md → src/risklens/analytics/attribution.py

## Import Cycles
- None detected.

## Communities (54 total, 5 thin omitted)

### Community 0 - "test_what_if.py"
Cohesion: 0.09
Nodes (26): run_what_if(), What-if trade (`trade_weights`, `compare_portfolios`), _aligned(), _checked_amount(), _checked_weights(), compare_portfolios(), trade_cost(), trade_weights() (+18 more)

### Community 1 - "pytest"
Cohesion: 0.18
Nodes (16): validate_price_history(), prices(), test_cost_bps_accepts_non_negative_basis_points(), test_cost_bps_rejects_bad_input(), test_date_range_rejects_bad_input(), test_price_history_allows_an_asset_with_no_observations(), test_price_history_keeps_missing_values_without_mutating_input(), test_price_history_rejects_bad_input() (+8 more)

### Community 2 - "simulate_portfolio"
Cohesion: 0.19
Nodes (20): simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility(), test_constant_history_is_deterministic() (+12 more)

### Community 3 - "test_data.py"
Cohesion: 0.21
Nodes (17): dates(), fetch(), history(), test_drops_dates_missing_for_any_ticker(), test_flat_single_ticker_response_is_named_after_ticker(), test_malformed_or_invalid_responses_raise_data_fetch_error(), test_price_history_and_fetch_prices_agree_on_shared_dates(), test_price_history_does_not_fill_missing_prices() (+9 more)

### Community 4 - "analyze_portfolio"
Cohesion: 0.09
Nodes (27): Architecture, analyze_portfolio(), to_returns(), validate_prices(), prices(), assert_same_metrics(), test_price_level_of_an_asset_does_not_change_metrics(), test_splitting_an_asset_across_identical_columns_changes_nothing() (+19 more)

### Community 5 - "efficient_frontier"
Cohesion: 0.14
Nodes (27): efficient_frontier(), EfficientFrontier, frontier_point_within_risk(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_estimates_inputs_and_solves_min_volatility_once(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_frontier_weights_are_long_only_and_metrics_match_engine() (+19 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (18): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_frontier_reuses_the_minimum_volatility_result(), test_frontier_solves_its_own_minimum_volatility_after_a_failure(), test_least_risky_current_portfolio_has_no_same_risk_point() (+10 more)

### Community 7 - "test_concentration.py"
Cohesion: 0.16
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 8 - "historical_cvar"
Cohesion: 0.16
Nodes (19): historical_cvar(), tail_risk_summary(), test_exactly_one_tail_observation_counts_as_sufficient(), test_non_numeric_confidence_raises_value_error(), test_numpy_and_python_floats_are_accepted(), test_summary_rejects_returns_with_nan(), series(), test_cvar_averages_returns_at_or_below_var_threshold() (+11 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.11
Nodes (28): estimate_inputs(), max_sharpe_portfolio(), make_prices(), random_portfolios(), test_max_sharpe_is_at_least_every_frontier_point(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved() (+20 more)

### Community 12 - "test_rolling.py"
Cohesion: 0.07
Nodes (43): Rolling risk metrics, _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility() (+35 more)

### Community 13 - "optimization.py"
Cohesion: 0.11
Nodes (9): Portfolio optimization, _min_volatility(), OptimizedPortfolio, _portfolio(), _reused_min_volatility_return(), _solve(), SolverDiagnostics, _target_return_solve() (+1 more)

### Community 14 - "test_metrics_regression.py"
Cohesion: 0.13
Nodes (16): drawdown_series(), dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates(), dated() (+8 more)

### Community 15 - "OptimizationError"
Cohesion: 0.21
Nodes (7): OptimizationError, test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error(), test_solver_failure_raises_optimization_error()

### Community 16 - "test_smoke.py"
Cohesion: 0.06
Nodes (20): chart_values(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results() (+12 more)

### Community 17 - "DataFetchError"
Cohesion: 0.13
Nodes (12): _close_prices(), DataFetchError, _download_close(), fetch_benchmark_prices(), fetch_price_history(), fetch_prices(), _parse_french_csv(), test_bad_date_range_is_rejected_before_download() (+4 more)

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.10
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.09
Nodes (14): cost_text(), dollar_change(), holding_inputs(), plain_text(), render_benchmark_ratios(), render_risk_attribution(), render_rolling(), render_shock_result() (+6 more)

### Community 20 - "_coverage_gaps"
Cohesion: 0.29
Nodes (3): _coverage_gaps(), _naive_dates(), _window()

### Community 21 - "stress_test"
Cohesion: 0.06
Nodes (47): custom_scenario(), _parse_date(), stress_test(), _weekdays_between(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates(), test_early_history_end_allows_at_most_one_missing_weekday() (+39 more)

### Community 22 - "test_simulation_memory.py"
Cohesion: 0.16
Nodes (8): assert_identical(), copying_simulation(), returns(), test_largest_supported_run_matches_the_copying_implementation(), test_peak_memory_stays_near_one_path_buffer(), test_same_seed_matches_the_copying_implementation_exactly(), test_terminal_returns_survive_the_in_place_percentile_partition(), test_zero_volatility_history_matches_the_copying_implementation()

### Community 23 - "shock_impact"
Cohesion: 0.14
Nodes (14): _regress(), _shared_returns(), shock_impact(), assets(), proxies(), test_a_holding_that_is_the_proxy_has_beta_one(), test_holding_moves_are_capped_at_a_total_loss(), test_only_shocked_proxies_enter_the_regression() (+6 more)

### Community 24 - "test_simulation.py"
Cohesion: 0.21
Nodes (11): history(), returns(), test_does_not_mutate_returns(), test_paths_start_at_one_on_last_date_and_move_forward(), test_percentiles_are_ordered_and_terminal_stats_agree(), test_rejects_bad_returns(), test_rejects_bad_settings(), test_same_seed_reproduces_and_new_seed_differs() (+3 more)

### Community 25 - "portfolio_returns"
Cohesion: 0.06
Nodes (41): render_stress_test(), _as_float_values(), _drifted_returns(), _portfolio_inputs(), portfolio_returns(), _rebalance_periods(), rebalance_turnover(), _turnover() (+33 more)

### Community 26 - "min_volatility_portfolio"
Cohesion: 0.18
Nodes (8): min_volatility_portfolio(), assert_kkt(), redundant_assets(), test_first_frontier_point_holds_the_min_volatility_weights(), test_max_sharpe_satisfies_kkt_conditions(), test_min_volatility_satisfies_kkt_with_a_binding_long_only_bound(), test_rescaling_one_price_column_leaves_weights_unchanged(), test_min_volatility_weights_ignore_risk_free_rate()

### Community 27 - "test_what_if_ui.py"
Cohesion: 0.25
Nodes (13): analyzed(), download(), expected_metrics(), prices(), simulate(), tables(), test_bad_trades_show_a_warning(), test_buying_a_new_ticker_downloads_it_for_the_same_dates() (+5 more)

### Community 28 - "test_simulation_regression.py"
Cohesion: 0.26
Nodes (7): history(), noisy(), test_break_even_paths_are_not_counted_as_losses(), test_duplicate_dates_and_worse_than_total_loss_are_rejected(), test_friday_history_continues_on_the_next_consecutive_weekdays(), test_percentile_bands_match_lognormal_quantiles(), test_seed_above_the_32_bit_range_is_rejected()

### Community 30 - "simulation_memory.py"
Cohesion: 0.31
Nodes (3): benchmark_returns(), main(), measure()

### Community 31 - "test_rebalance_ui.py"
Cohesion: 0.10
Nodes (20): analyze(), card_values(), download(), prices(), spy(), test_controls_default_to_daily_rebalancing_without_costs(), test_daily_cost_free_optimization_has_no_baseline_note(), test_default_analysis_passes_daily_and_zero_cost() (+12 more)

### Community 32 - "validate_date_range"
Cohesion: 0.19
Nodes (8): _parse_date(), validate_date_range(), test_matching_time_zones_are_accepted(), test_missing_or_nonsense_start_is_rejected(), test_mixed_time_zones_raise_value_error(), test_today_is_a_valid_start_date(), test_tomorrow_is_rejected_as_future(), test_date_range_parses_strings_and_dates()

### Community 34 - "pandas"
Cohesion: 0.25
Nodes (16): compare_to_benchmark(), dates(), test_both_curves_start_at_one_on_first_shared_date(), test_cumulative_wealth_compounds_from_one(), test_does_not_mutate_inputs(), test_drops_dates_with_missing_prices(), test_fetch_benchmark_prices_downloads_spy_adjusted_close(), test_portfolio_equal_to_benchmark_has_beta_one_and_no_tracking_error() (+8 more)

### Community 35 - "test_holdings.py"
Cohesion: 0.05
Nodes (40): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Custom shocks (`shock_impact`), Features, File structure, Historical VaR and CVaR (+32 more)

### Community 36 - "test_shocks_ui.py"
Cohesion: 0.27
Nodes (9): analyzed(), download(), prices(), shocked(), test_apply_waits_for_a_non_zero_move(), test_changing_a_move_hides_the_old_estimate(), test_download_failure_shows_a_warning(), test_shock_matches_the_api_and_downloads_only_the_proxy() (+1 more)

### Community 37 - "numpy"
Cohesion: 0.30
Nodes (10): geometric_mean(), prices_from(), statistics(), test_capture_compares_geometric_mean_returns_on_up_and_down_days(), test_capture_is_nan_without_up_or_down_days_and_ignores_flat_days(), test_gaining_on_down_days_gives_negative_downside_capture(), test_information_ratio_is_annual_excess_return_per_unit_of_tracking_error(), test_information_ratio_is_nan_when_the_portfolio_is_the_benchmark() (+2 more)

### Community 38 - "test_holdings_ui.py"
Cohesion: 0.16
Nodes (23): analyze(), captions(), download(), enter_holdings(), prices(), test_bad_csv_lists_its_rows_and_blocks_analysis(), test_cards_have_no_dollar_amounts_without_a_portfolio_value(), test_changing_the_file_or_holdings_type_clears_old_results() (+15 more)

### Community 39 - "factor_exposure"
Cohesion: 0.22
Nodes (7): factor_exposure(), factors(), test_group_breakdown_rejects_unlabelled_ticker(), test_group_breakdown_sums_weights_and_risk_by_label(), test_noise_lowers_r_squared_and_only_shared_dates_are_used(), test_recovers_known_betas_and_alpha_without_noise(), test_rejects_short_overlap_missing_columns_and_constant_returns()

### Community 40 - "benchmark_statistics"
Cohesion: 0.23
Nodes (4): _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, _capture()

### Community 41 - "historical_var"
Cohesion: 0.10
Nodes (27): annualized_return(), annualized_volatility(), cumulative_wealth(), historical_var(), risk_contributions(), sharpe_ratio(), _validate_dated_returns(), _validate_returns() (+19 more)

### Community 42 - "value_at_risk.py"
Cohesion: 0.23
Nodes (4): _cornish_fisher_z(), _skew_kurtosis(), _var_rows(), _whole_number()

### Community 43 - "data.py"
Cohesion: 0.18
Nodes (7): Factor and sector exposure, _download_french(), fetch_classifications(), fetch_factors(), test_download_errors_and_files_without_data_raise_data_fetch_error(), test_parses_percent_tables_into_fractions_and_joins_momentum(), zipped()

### Community 44 - "test_risk_metrics_ui.py"
Cohesion: 0.21
Nodes (16): analyze(), cards(), download(), prices(), serve(), test_backtest_explains_when_the_period_is_shorter_than_the_window(), test_backtest_flags_var_that_was_too_low_or_too_high(), test_backtest_table_matches_var_backtest_for_the_chosen_window() (+8 more)

### Community 45 - "test_value_at_risk.py"
Cohesion: 0.09
Nodes (32): render_tail_risk(), VaR models and backtesting, _validate_confidence(), cornish_fisher_var(), kupiec_test(), normal_var(), rolling_var(), _validate_rolling_inputs() (+24 more)

### Community 46 - "sortino_ratio"
Cohesion: 0.20
Nodes (13): calmar_ratio(), sortino_ratio(), dated(), test_analyze_portfolio_reports_sortino_and_calmar_on_its_daily_returns(), test_bigger_gains_raise_sortino_in_proportion_but_not_sharpe(), test_calmar_divides_compound_annual_growth_by_the_worst_drawdown(), test_calmar_is_nan_without_a_drawdown(), test_calmar_is_negative_when_the_portfolio_lost_money() (+5 more)

### Community 47 - "render_risk_sources"
Cohesion: 0.22
Nodes (4): comparison_table(), format_number(), render_factor_exposure(), render_risk_sources()

### Community 48 - "test_benchmark_regression.py"
Cohesion: 0.22
Nodes (5): prices_from(), test_benchmark_price_level_does_not_change_statistics(), test_flat_portfolio_has_zero_beta_and_undefined_correlation(), test_half_benchmark_half_cash_has_beta_one_half(), test_scaled_benchmark_returns_give_that_beta()

### Community 49 - "render_var_backtest"
Cohesion: 0.33
Nodes (3): backtest_result(), model_var(), render_var_backtest()

### Community 50 - "test_benchmark_audit.py"
Cohesion: 0.38
Nodes (3): series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta()

### Community 51 - "render_frontier"
Cohesion: 0.33
Nodes (3): render_frontier(), render_optimization(), render_optimization_results()

### Community 52 - "analytics/__init__.py"
Cohesion: 0.09
Nodes (15): Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), Rebalancing and trading costs, FactorExposure, group_breakdown(), PortfolioMetrics, max_drawdown(), ShockImpact (+7 more)

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 392 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `analytics/__init__.py` to `test_what_if.py`, `pytest`, `simulate_portfolio`, `analyze_portfolio`, `efficient_frontier`, `test_concentration.py`, `historical_cvar`, `test_optimization.py`, `test_rolling.py`, `optimization.py`, `test_metrics_regression.py`, `OptimizationError`, `DataFetchError`, `stress_test`, `shock_impact`, `portfolio_returns`, `min_volatility_portfolio`, `validate_date_range`, `pandas`, `test_holdings.py`, `factor_exposure`, `benchmark_statistics`, `historical_var`, `test_value_at_risk.py`, `sortino_ratio`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `Analytics API` (e.g. with `factor_exposure()` and `FactorExposure`) actually correct?**
  _`Analytics API` has 71 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_what_if.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09302325581395349 - nodes in this community are weakly interconnected._
- **Why does `efficient_frontier()` connect `efficient_frontier` to `pandas`, `numpy`, `test_risk_ui.py`, `test_optimization.py`, `optimization.py`, `OptimizationError`, `render_frontier`, `analytics/__init__.py`, `min_volatility_portfolio`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `analyze_portfolio` be split into smaller, more focused modules?**
  _Cohesion score 0.0898989898989899 - nodes in this community are weakly interconnected._