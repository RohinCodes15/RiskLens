# Graph Report - RiskLens  (2026-11-03)

## Corpus Check
- 76 files · ~56,820 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 1487 nodes · 4556 edges · 53 communities (48 shown, 5 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 706 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `436afa0d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- historical_var
- validate_weights
- test_simulation_audit.py
- test_data.py
- analyze_portfolio
- efficient_frontier
- test_risk_ui.py
- test_concentration.py
- fit_garch
- risklens
- test_optimization.py
- test_rolling.py
- optimization.py
- test_metrics_regression.py
- OptimizationError
- test_smoke.py
- data.py
- test_stress_history_ui.py
- app.py
- rolling.py
- stress_test
- test_simulation_memory.py
- shock_impact
- simulate_portfolio
- portfolio_returns
- min_volatility_portfolio
- test_what_if_ui.py
- test_simulation_regression.py
- custom_scenario
- simulation_memory.py
- test_rebalance_ui.py
- validation.py
- chart_values
- pandas
- test_holdings.py
- numpy
- test_benchmark_ratios.py
- test_holdings_ui.py
- test_simulation_tails_ui.py
- test_stress_history.py
- pytest
- annualized_volatility
- drawdown_series
- test_risk_metrics_ui.py
- test_value_at_risk.py
- sortino_ratio
- test_rolling_regression.py
- _parse_date
- test_stress_dropped_days.py
- _draws
- render_frontier
- analytics/__init__.py

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 77 edges
2. `analyze_portfolio()` - 64 edges
3. `simulate_portfolio()` - 64 edges
4. `stress_test()` - 63 edges
5. `efficient_frontier()` - 50 edges
6. `portfolio_returns()` - 49 edges
7. `five_assets()` - 46 edges
8. `to_returns()` - 34 edges
9. `custom_scenario()` - 33 edges
10. `min_volatility_portfolio()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Coding standards` --references--> `DataFetchError`  [INFERRED]
  AGENTS.md → src/risklens/data.py
- `Usage` --references--> `fetch_price_history()`  [INFERRED]
  README.md → src/risklens/data.py
- `Factor and sector exposure` --references--> `FactorExposure`  [INFERRED]
  README.md → src/risklens/analytics/attribution.py
- `Analytics API` --references--> `factor_exposure()`  [INFERRED]
  README.md → src/risklens/analytics/attribution.py

## Import Cycles
- None detected.

## Communities (53 total, 5 thin omitted)

### Community 0 - "historical_var"
Cohesion: 0.06
Nodes (46): run_what_if(), What-if trade (`trade_weights`, `compare_portfolios`), historical_cvar(), historical_var(), tail_risk_summary(), _aligned(), _checked_amount(), _checked_weights() (+38 more)

### Community 1 - "validate_weights"
Cohesion: 0.09
Nodes (23): validate_cost_bps(), validate_price_history(), validate_prices(), validate_tickers(), validate_weights(), prices(), test_cost_bps_accepts_non_negative_basis_points(), test_cost_bps_rejects_bad_input() (+15 more)

### Community 2 - "test_simulation_audit.py"
Cohesion: 0.19
Nodes (18): dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility(), test_constant_history_is_deterministic(), test_every_path_starts_at_wealth_one_on_the_last_historical_date(), test_insufficient_history_is_rejected() (+10 more)

### Community 3 - "test_data.py"
Cohesion: 0.16
Nodes (21): fetch_price_history(), dates(), fetch(), history(), test_drops_dates_missing_for_any_ticker(), test_empty_ticker_list_is_rejected_before_download(), test_flat_single_ticker_response_is_named_after_ticker(), test_malformed_or_invalid_responses_raise_data_fetch_error() (+13 more)

### Community 4 - "analyze_portfolio"
Cohesion: 0.10
Nodes (26): Architecture, analyze_portfolio(), to_returns(), prices(), assert_same_metrics(), test_price_level_of_an_asset_does_not_change_metrics(), test_splitting_an_asset_across_identical_columns_changes_nothing(), two_assets() (+18 more)

### Community 5 - "efficient_frontier"
Cohesion: 0.14
Nodes (27): efficient_frontier(), EfficientFrontier, frontier_point_within_risk(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_estimates_inputs_and_solves_min_volatility_once(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_frontier_weights_are_long_only_and_metrics_match_engine() (+19 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (18): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_frontier_reuses_the_minimum_volatility_result(), test_frontier_solves_its_own_minimum_volatility_after_a_failure(), test_least_risky_current_portfolio_has_no_same_risk_point() (+10 more)

### Community 7 - "test_concentration.py"
Cohesion: 0.16
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 8 - "fit_garch"
Cohesion: 0.07
Nodes (33): render_volatility_forecast(), Volatility forecasts, _checked_returns(), _conditional_variance(), ewma_volatility(), fit_garch(), garch_forecast(), GarchFit (+25 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.11
Nodes (28): estimate_inputs(), max_sharpe_portfolio(), make_prices(), random_portfolios(), test_max_sharpe_is_at_least_every_frontier_point(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved() (+20 more)

### Community 12 - "test_rolling.py"
Cohesion: 0.15
Nodes (25): dated(), noisy(), test_constant_window_has_exactly_zero_volatility(), test_drawdown_counts_the_level_before_the_window(), test_drawdown_is_never_positive_and_total_loss_is_minus_one(), test_drawdown_matches_drawdown_series_on_each_window(), test_drawdown_uses_local_peak_not_all_time_high(), test_exactly_window_returns_gives_one_value() (+17 more)

### Community 13 - "optimization.py"
Cohesion: 0.11
Nodes (9): Portfolio optimization, _min_volatility(), OptimizedPortfolio, _portfolio(), _reused_min_volatility_return(), _solve(), SolverDiagnostics, _target_return_solve() (+1 more)

### Community 14 - "test_metrics_regression.py"
Cohesion: 0.24
Nodes (9): dated(), noisy(), test_risk_contributions_ignore_the_scale_of_returns(), test_sharpe_ratio_ignores_leverage_at_a_zero_risk_free_rate(), test_tail_risk_ignores_the_order_of_returns(), test_tail_risk_rises_with_confidence(), test_tail_risk_scales_with_exposure(), test_total_loss_day_wipes_out_wealth_for_good() (+1 more)

### Community 15 - "OptimizationError"
Cohesion: 0.21
Nodes (7): OptimizationError, test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error(), test_solver_failure_raises_optimization_error()

### Community 16 - "test_smoke.py"
Cohesion: 0.08
Nodes (17): download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results(), test_historical_scenarios_use_their_own_download_window() (+9 more)

### Community 17 - "data.py"
Cohesion: 0.10
Nodes (16): render_risk_sources(), Factor and sector exposure, _close_prices(), DataFetchError, _download_close(), _download_french(), fetch_benchmark_prices(), fetch_classifications() (+8 more)

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.10
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.06
Nodes (21): backtest_result(), comparison_table(), cost_text(), dollar_change(), format_number(), holding_inputs(), model_var(), plain_text() (+13 more)

### Community 20 - "rolling.py"
Cohesion: 0.16
Nodes (13): Rolling risk metrics, _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility() (+5 more)

### Community 21 - "stress_test"
Cohesion: 0.16
Nodes (17): stress_test(), prices(), test_drawdown_is_peak_to_trough_inside_the_window(), test_every_short_asset_is_named_in_column_order(), test_exactly_three_common_prices_is_available(), test_reordering_assets_with_their_weights_changes_nothing(), test_single_asset_return_is_its_price_ratio(), test_asset_listed_after_window_start_is_unavailable() (+9 more)

### Community 22 - "test_simulation_memory.py"
Cohesion: 0.13
Nodes (9): _future_dates(), assert_identical(), copying_simulation(), returns(), test_largest_supported_run_matches_the_copying_implementation(), test_peak_memory_stays_near_one_path_buffer(), test_same_seed_matches_the_copying_implementation_exactly(), test_terminal_returns_survive_the_in_place_percentile_partition() (+1 more)

### Community 23 - "shock_impact"
Cohesion: 0.08
Nodes (24): _active_shocks(), _regress(), _shared_returns(), shock_impact(), assets(), proxies(), test_a_holding_that_is_the_proxy_has_beta_one(), test_holding_moves_are_capped_at_a_total_loss() (+16 more)

### Community 24 - "simulate_portfolio"
Cohesion: 0.15
Nodes (15): _estimate_parameters(), simulate_portfolio(), _validate_int(), history(), returns(), test_student_t_needs_fat_tails_and_four_returns(), test_does_not_mutate_returns(), test_paths_start_at_one_on_last_date_and_move_forward() (+7 more)

### Community 25 - "portfolio_returns"
Cohesion: 0.06
Nodes (40): _as_float_values(), _drifted_returns(), _portfolio_inputs(), portfolio_returns(), _rebalance_periods(), rebalance_turnover(), _turnover(), prices() (+32 more)

### Community 26 - "min_volatility_portfolio"
Cohesion: 0.18
Nodes (8): min_volatility_portfolio(), assert_kkt(), redundant_assets(), test_first_frontier_point_holds_the_min_volatility_weights(), test_max_sharpe_satisfies_kkt_conditions(), test_min_volatility_satisfies_kkt_with_a_binding_long_only_bound(), test_rescaling_one_price_column_leaves_weights_unchanged(), test_min_volatility_weights_ignore_risk_free_rate()

### Community 27 - "test_what_if_ui.py"
Cohesion: 0.25
Nodes (13): analyzed(), download(), expected_metrics(), prices(), simulate(), tables(), test_bad_trades_show_a_warning(), test_buying_a_new_ticker_downloads_it_for_the_same_dates() (+5 more)

### Community 28 - "test_simulation_regression.py"
Cohesion: 0.29
Nodes (7): history(), noisy(), test_break_even_paths_are_not_counted_as_losses(), test_duplicate_dates_and_worse_than_total_loss_are_rejected(), test_friday_history_continues_on_the_next_consecutive_weekdays(), test_percentile_bands_match_lognormal_quantiles(), test_seed_above_the_32_bit_range_is_rejected()

### Community 29 - "custom_scenario"
Cohesion: 0.19
Nodes (14): render_stress_test(), custom_scenario(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_early_history_end_allows_at_most_one_missing_weekday(), test_holiday_monday_end_with_friday_last_price_is_available(), test_invalid_scenarios_are_rejected_at_construction(), test_late_listing_allows_at_most_one_missing_weekday() (+6 more)

### Community 30 - "simulation_memory.py"
Cohesion: 0.31
Nodes (3): benchmark_returns(), main(), measure()

### Community 31 - "test_rebalance_ui.py"
Cohesion: 0.10
Nodes (20): analyze(), card_values(), download(), prices(), spy(), test_controls_default_to_daily_rebalancing_without_costs(), test_daily_cost_free_optimization_has_no_baseline_note(), test_default_analysis_passes_daily_and_zero_cost() (+12 more)

### Community 32 - "validation.py"
Cohesion: 0.16
Nodes (7): _parse_date(), validate_date_range(), test_matching_time_zones_are_accepted(), test_missing_or_nonsense_start_is_rejected(), test_mixed_time_zones_raise_value_error(), test_today_is_a_valid_start_date(), test_tomorrow_is_rejected_as_future()

### Community 33 - "chart_values"
Cohesion: 0.12
Nodes (5): chart_values(), app_data(), test_confidence_switch_uses_api_and_actual_histogram(), test_invalid_tail_data_hides_risk_results(), test_small_sample_warning_and_zero_returns()

### Community 34 - "pandas"
Cohesion: 0.06
Nodes (39): Rebalancing and trading costs, factor_exposure(), group_breakdown(), _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, _capture(), compare_to_benchmark() (+31 more)

### Community 35 - "test_holdings.py"
Cohesion: 0.06
Nodes (38): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Custom shocks (`shock_impact`), Features, File structure, Historical VaR and CVaR (+30 more)

### Community 36 - "numpy"
Cohesion: 0.18
Nodes (13): one_day_draws(), returns(), test_bootstrap_fills_every_block_including_a_partial_one(), test_bootstrap_only_reuses_past_days(), test_bootstrap_paths_sum_resampled_days(), test_constant_history_gives_one_flat_path(), test_fat_tailed_models_are_reproducible(), test_fat_tails_widen_the_lower_band() (+5 more)

### Community 37 - "test_benchmark_ratios.py"
Cohesion: 0.30
Nodes (9): geometric_mean(), prices_from(), statistics(), test_capture_compares_geometric_mean_returns_on_up_and_down_days(), test_capture_is_nan_without_up_or_down_days_and_ignores_flat_days(), test_gaining_on_down_days_gives_negative_downside_capture(), test_information_ratio_is_annual_excess_return_per_unit_of_tracking_error(), test_information_ratio_is_nan_when_the_portfolio_is_the_benchmark() (+1 more)

### Community 38 - "test_holdings_ui.py"
Cohesion: 0.16
Nodes (23): analyze(), captions(), download(), enter_holdings(), prices(), test_bad_csv_lists_its_rows_and_blocks_analysis(), test_cards_have_no_dollar_amounts_without_a_portfolio_value(), test_changing_the_file_or_holdings_type_clears_old_results() (+15 more)

### Community 39 - "test_simulation_tails_ui.py"
Cohesion: 0.22
Nodes (8): download(), expected(), prices(), run_with(), test_bootstrap_caption_explains_its_limit(), test_choice_reaches_the_engine_and_chart(), test_student_t_caption_reports_degrees_of_freedom(), test_student_t_without_fat_tails_shows_an_error()

### Community 40 - "test_stress_history.py"
Cohesion: 0.32
Nodes (10): history(), test_common_dates_hid_which_asset_listed_late(), test_custom_window_after_listing_is_available(), test_delisted_ticker_reports_the_scenario_end(), test_every_scenario_names_only_the_late_listing(), test_fully_covered_portfolio_matches_common_date_results(), test_missing_day_inside_window_is_dropped_not_reported(), test_recent_ipo_is_the_only_asset_blamed() (+2 more)

### Community 41 - "pytest"
Cohesion: 0.19
Nodes (17): risk_contributions(), series(), test_annualized_return_and_volatility_use_252_days(), test_hedging_asset_has_negative_risk_contribution(), test_historical_var_is_negative_when_every_day_gains(), test_historical_var_is_positive_loss_at_confidence(), test_historical_var_rejects_bad_confidence(), test_metrics_reject_bad_returns() (+9 more)

### Community 42 - "annualized_volatility"
Cohesion: 0.14
Nodes (10): annualized_return(), annualized_volatility(), cumulative_wealth(), sharpe_ratio(), _validate_dated_returns(), _validate_returns(), _validate_rolling_inputs(), test_all_weight_on_one_asset_gives_that_assets_metrics() (+2 more)

### Community 43 - "drawdown_series"
Cohesion: 0.29
Nodes (7): drawdown_series(), dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates()

### Community 44 - "test_risk_metrics_ui.py"
Cohesion: 0.21
Nodes (16): analyze(), cards(), download(), prices(), serve(), test_backtest_explains_when_the_period_is_shorter_than_the_window(), test_backtest_flags_var_that_was_too_low_or_too_high(), test_backtest_table_matches_var_backtest_for_the_chosen_window() (+8 more)

### Community 45 - "test_value_at_risk.py"
Cohesion: 0.07
Nodes (35): render_tail_risk(), VaR models and backtesting, _validate_confidence(), cornish_fisher_var(), _cornish_fisher_z(), kupiec_test(), normal_var(), rolling_var() (+27 more)

### Community 46 - "sortino_ratio"
Cohesion: 0.20
Nodes (13): calmar_ratio(), sortino_ratio(), dated(), test_analyze_portfolio_reports_sortino_and_calmar_on_its_daily_returns(), test_bigger_gains_raise_sortino_in_proportion_but_not_sharpe(), test_calmar_divides_compound_annual_growth_by_the_worst_drawdown(), test_calmar_is_nan_without_a_drawdown(), test_calmar_is_negative_when_the_portfolio_lost_money() (+5 more)

### Community 47 - "test_rolling_regression.py"
Cohesion: 0.29
Nodes (5): shocked(), test_max_drawdown_holds_the_drop_for_exactly_one_window(), test_rolling_sharpe_ignores_leverage_at_a_zero_risk_free_rate(), test_volatility_is_raised_only_while_the_shock_is_in_the_window(), windows_containing_shock()

### Community 51 - "render_frontier"
Cohesion: 0.33
Nodes (3): render_frontier(), render_optimization(), render_optimization_results()

### Community 52 - "analytics/__init__.py"
Cohesion: 0.08
Nodes (15): Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), FactorExposure, PortfolioMetrics, max_drawdown(), ShockImpact, MonteCarloResult, _coverage_gaps() (+7 more)

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 422 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `analytics/__init__.py` to `historical_var`, `validate_weights`, `test_data.py`, `analyze_portfolio`, `efficient_frontier`, `test_concentration.py`, `fit_garch`, `test_optimization.py`, `optimization.py`, `OptimizationError`, `data.py`, `rolling.py`, `stress_test`, `shock_impact`, `simulate_portfolio`, `portfolio_returns`, `min_volatility_portfolio`, `custom_scenario`, `validation.py`, `pandas`, `test_holdings.py`, `pytest`, `annualized_volatility`, `drawdown_series`, `test_value_at_risk.py`, `sortino_ratio`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 76 inferred relationships involving `Analytics API` (e.g. with `factor_exposure()` and `FactorExposure`) actually correct?**
  _`Analytics API` has 76 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `historical_var` be split into smaller, more focused modules?**
  _Cohesion score 0.05960755275823769 - nodes in this community are weakly interconnected._
- **Why does `RiskLens Quant` connect `test_holdings.py` to `pandas`, `fit_garch`, `optimization.py`, `test_value_at_risk.py`, `data.py`, `rolling.py`, `analytics/__init__.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `analyze_portfolio()` (e.g. with `Architecture` and `Analytics API`) actually correct?**
  _`analyze_portfolio()` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Should `validate_weights` be split into smaller, more focused modules?**
  _Cohesion score 0.09009009009009009 - nodes in this community are weakly interconnected._