# Graph Report - RiskLens  (2026-11-03)

## Corpus Check
- 65 files · ~131,887 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 1250 nodes · 3851 edges · 49 communities (44 shown, 5 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 602 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f1428a35`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fetch_price_history
- validation.py
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
- fetch_prices
- test_stress_history_ui.py
- app.py
- StressScenario
- stress_test
- test_simulation_memory.py
- Architecture
- test_simulation.py
- portfolio_returns
- min_volatility_portfolio
- estimate_inputs
- test_simulation_regression.py
- simulation.py
- simulation_memory.py
- test_rebalance_ui.py
- _validate_points
- test_invalid_tail_data_hides_risk_results
- pandas
- test_holdings.py
- numpy
- test_holdings_ui.py
- test_drawdown.py
- test_tail_risk_audit.py
- test_metrics.py
- test_engine_regression.py
- data.py
- test_risk_metrics_ui.py
- test_value_at_risk.py
- sortino_ratio
- RiskLens Quant
- analyze_portfolio
- analytics/__init__.py

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 66 edges
2. `stress_test()` - 63 edges
3. `analyze_portfolio()` - 56 edges
4. `efficient_frontier()` - 50 edges
5. `simulate_portfolio()` - 50 edges
6. `portfolio_returns()` - 49 edges
7. `five_assets()` - 46 edges
8. `custom_scenario()` - 33 edges
9. `to_returns()` - 32 edges
10. `min_volatility_portfolio()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Coding standards` --references--> `DataFetchError`  [INFERRED]
  AGENTS.md → src/risklens/data.py
- `Factor and sector exposure` --references--> `FactorExposure`  [INFERRED]
  README.md → src/risklens/analytics/attribution.py
- `Analytics API` --references--> `factor_exposure()`  [INFERRED]
  README.md → src/risklens/analytics/attribution.py

## Import Cycles
- None detected.

## Communities (49 total, 5 thin omitted)

### Community 0 - "fetch_price_history"
Cohesion: 0.22
Nodes (7): render_stress_test(), Monte Carlo (`simulate_portfolio`), Simulation and stress testing, Usage, fetch_price_history(), test_price_history_download_exception_becomes_data_fetch_error(), test_price_history_rejects_bad_requests_before_download()

### Community 1 - "validation.py"
Cohesion: 0.19
Nodes (15): validate_price_history(), prices(), test_cost_bps_accepts_non_negative_basis_points(), test_cost_bps_rejects_bad_input(), test_date_range_rejects_bad_input(), test_price_history_allows_an_asset_with_no_observations(), test_price_history_keeps_missing_values_without_mutating_input(), test_price_history_rejects_bad_input() (+7 more)

### Community 2 - "simulate_portfolio"
Cohesion: 0.19
Nodes (20): simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility(), test_constant_history_is_deterministic() (+12 more)

### Community 3 - "data.py"
Cohesion: 0.21
Nodes (17): dates(), fetch(), history(), test_drops_dates_missing_for_any_ticker(), test_flat_single_ticker_response_is_named_after_ticker(), test_malformed_or_invalid_responses_raise_data_fetch_error(), test_price_history_and_fetch_prices_agree_on_shared_dates(), test_price_history_does_not_fill_missing_prices() (+9 more)

### Community 4 - "analyze_portfolio"
Cohesion: 0.19
Nodes (14): to_returns(), prices(), spy(), test_benchmark_defaults_are_unchanged(), test_benchmark_growth_uses_rebalance_and_cost(), test_benchmark_statistics_use_rebalance_and_cost(), test_buy_and_hold_has_no_turnover(), test_costs_lower_engine_return_but_not_turnover() (+6 more)

### Community 5 - "efficient_frontier"
Cohesion: 0.16
Nodes (24): render_optimization(), efficient_frontier(), frontier_point_within_risk(), min_volatility_portfolio(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_weights_are_long_only_and_metrics_match_engine(), test_invalid_point_counts_are_rejected(), test_invalid_risk_free_rate_is_rejected() (+16 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (18): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_frontier_reuses_the_minimum_volatility_result(), test_frontier_solves_its_own_minimum_volatility_after_a_failure(), test_least_risky_current_portfolio_has_no_same_risk_point() (+10 more)

### Community 7 - "test_concentration.py"
Cohesion: 0.14
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 8 - "historical_cvar"
Cohesion: 0.23
Nodes (15): historical_cvar(), tail_risk_summary(), series(), test_cvar_averages_returns_at_or_below_var_threshold(), test_cvar_does_not_mutate_input(), test_cvar_is_negative_when_every_day_gains(), test_cvar_is_never_below_var(), test_cvar_rejects_bad_confidence() (+7 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.11
Nodes (26): max_sharpe_portfolio(), test_no_sampled_portfolio_beats_a_frontier_point(), make_prices(), random_portfolios(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_diagnostics_report_a_converged_full_rank_solve(), test_duplicate_asset_is_flagged_singular_but_still_solved(), test_infeasible_solver_output_raises_optimization_error() (+18 more)

### Community 12 - "pytest"
Cohesion: 0.07
Nodes (42): _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility(), _validate_window() (+34 more)

### Community 13 - "optimization.py"
Cohesion: 0.14
Nodes (7): Portfolio optimization, _min_volatility(), OptimizedPortfolio, _portfolio(), _reused_min_volatility_return(), _solve(), _target_return_solve()

### Community 14 - "test_metrics_regression.py"
Cohesion: 0.26
Nodes (8): dated(), noisy(), test_risk_contributions_ignore_the_scale_of_returns(), test_sharpe_ratio_ignores_leverage_at_a_zero_risk_free_rate(), test_tail_risk_ignores_the_order_of_returns(), test_tail_risk_rises_with_confidence(), test_tail_risk_scales_with_exposure(), three_assets()

### Community 15 - "OptimizationError"
Cohesion: 0.24
Nodes (7): OptimizationError, test_frontier_estimates_inputs_and_solves_min_volatility_once(), test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error()

### Community 16 - "submit"
Cohesion: 0.06
Nodes (20): chart_values(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results() (+12 more)

### Community 17 - "fetch_prices"
Cohesion: 0.25
Nodes (5): fetch_benchmark_prices(), fetch_prices(), test_bad_date_range_is_rejected_before_download(), test_download_exception_becomes_data_fetch_error(), test_empty_ticker_list_is_rejected_before_download()

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.10
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.07
Nodes (16): backtest_result(), cost_text(), dollar_change(), holding_inputs(), model_var(), plain_text(), render_benchmark_ratios(), render_factor_exposure() (+8 more)

### Community 20 - "StressScenario"
Cohesion: 0.24
Nodes (4): _coverage_gaps(), _naive_dates(), StressScenario, _window()

### Community 21 - "stress_test"
Cohesion: 0.06
Nodes (47): custom_scenario(), _parse_date(), stress_test(), _weekdays_between(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates(), test_early_history_end_allows_at_most_one_missing_weekday() (+39 more)

### Community 22 - "test_simulation_memory.py"
Cohesion: 0.16
Nodes (8): assert_identical(), copying_simulation(), returns(), test_largest_supported_run_matches_the_copying_implementation(), test_peak_memory_stays_near_one_path_buffer(), test_same_seed_matches_the_copying_implementation_exactly(), test_terminal_returns_survive_the_in_place_percentile_partition(), test_zero_volatility_history_matches_the_copying_implementation()

### Community 23 - "Architecture"
Cohesion: 0.29
Nodes (5): Agent rules, AGENTS.md — RiskLens Quant, Architecture, Coding standards, Ownership

### Community 24 - "test_simulation.py"
Cohesion: 0.21
Nodes (11): history(), returns(), test_does_not_mutate_returns(), test_paths_start_at_one_on_last_date_and_move_forward(), test_percentiles_are_ordered_and_terminal_stats_agree(), test_rejects_bad_returns(), test_rejects_bad_settings(), test_same_seed_reproduces_and_new_seed_differs() (+3 more)

### Community 25 - "portfolio_returns"
Cohesion: 0.06
Nodes (40): _as_float_values(), _drifted_returns(), _portfolio_inputs(), portfolio_returns(), _rebalance_periods(), rebalance_turnover(), _turnover(), prices() (+32 more)

### Community 26 - "min_volatility_portfolio"
Cohesion: 0.18
Nodes (8): assert_kkt(), redundant_assets(), test_first_frontier_point_holds_the_min_volatility_weights(), test_max_sharpe_is_at_least_every_frontier_point(), test_max_sharpe_satisfies_kkt_conditions(), test_min_volatility_satisfies_kkt_with_a_binding_long_only_bound(), test_rescaling_one_price_column_leaves_weights_unchanged(), test_risk_free_rate_changes_only_the_frontier_sharpe_column()

### Community 27 - "estimate_inputs"
Cohesion: 0.33
Nodes (5): estimate_inputs(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_runs_from_min_volatility_to_best_single_asset(), test_estimate_inputs_annualizes_mean_and_sample_covariance(), test_estimate_inputs_needs_more_returns_than_assets()

### Community 28 - "test_simulation_regression.py"
Cohesion: 0.26
Nodes (7): history(), noisy(), test_break_even_paths_are_not_counted_as_losses(), test_duplicate_dates_and_worse_than_total_loss_are_rejected(), test_friday_history_continues_on_the_next_consecutive_weekdays(), test_percentile_bands_match_lognormal_quantiles(), test_seed_above_the_32_bit_range_is_rejected()

### Community 30 - "simulation_memory.py"
Cohesion: 0.31
Nodes (3): benchmark_returns(), main(), measure()

### Community 31 - "test_rebalance_ui.py"
Cohesion: 0.10
Nodes (20): analyze(), card_values(), download(), prices(), spy(), test_controls_default_to_daily_rebalancing_without_costs(), test_daily_cost_free_optimization_has_no_baseline_note(), test_default_analysis_passes_daily_and_zero_cost() (+12 more)

### Community 34 - "pandas"
Cohesion: 0.05
Nodes (43): factor_exposure(), group_breakdown(), _aligned_returns(), benchmark_statistics(), _capture(), compare_to_benchmark(), _parse_date(), validate_date_range() (+35 more)

### Community 35 - "test_holdings.py"
Cohesion: 0.10
Nodes (20): holdings_to_weights(), parse_holdings_csv(), _parse_row(), validate_tickers(), prices(), test_accepts_excel_bytes_extra_columns_and_blank_lines(), test_dollar_values_ignore_prices(), test_lists_every_bad_row_including_repeated_tickers() (+12 more)

### Community 37 - "numpy"
Cohesion: 0.33
Nodes (9): geometric_mean(), prices_from(), statistics(), test_capture_compares_geometric_mean_returns_on_up_and_down_days(), test_capture_is_nan_without_up_or_down_days_and_ignores_flat_days(), test_gaining_on_down_days_gives_negative_downside_capture(), test_information_ratio_is_annual_excess_return_per_unit_of_tracking_error(), test_information_ratio_is_nan_when_the_portfolio_is_the_benchmark() (+1 more)

### Community 38 - "test_holdings_ui.py"
Cohesion: 0.16
Nodes (23): analyze(), captions(), download(), enter_holdings(), prices(), test_bad_csv_lists_its_rows_and_blocks_analysis(), test_cards_have_no_dollar_amounts_without_a_portfolio_value(), test_changing_the_file_or_holdings_type_clears_old_results() (+15 more)

### Community 39 - "test_drawdown.py"
Cohesion: 0.29
Nodes (6): dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates()

### Community 40 - "test_tail_risk_audit.py"
Cohesion: 0.33
Nodes (4): test_exactly_one_tail_observation_counts_as_sufficient(), test_non_numeric_confidence_raises_value_error(), test_numpy_and_python_floats_are_accepted(), test_summary_rejects_returns_with_nan()

### Community 41 - "test_metrics.py"
Cohesion: 0.12
Nodes (24): annualized_return(), annualized_volatility(), historical_var(), risk_contributions(), sharpe_ratio(), _validate_returns(), test_portfolio_return_is_weighted_but_volatility_is_diversified(), series() (+16 more)

### Community 42 - "test_engine_regression.py"
Cohesion: 0.26
Nodes (7): analyze_portfolio(), PortfolioMetrics, assert_same_metrics(), test_all_weight_on_one_asset_gives_that_assets_metrics(), test_price_level_of_an_asset_does_not_change_metrics(), test_splitting_an_asset_across_identical_columns_changes_nothing(), two_assets()

### Community 43 - "data.py"
Cohesion: 0.16
Nodes (9): _close_prices(), DataFetchError, _download_close(), _download_french(), fetch_factors(), _parse_french_csv(), test_download_errors_and_files_without_data_raise_data_fetch_error(), test_parses_percent_tables_into_fractions_and_joins_momentum() (+1 more)

### Community 44 - "test_risk_metrics_ui.py"
Cohesion: 0.21
Nodes (16): analyze(), cards(), download(), prices(), serve(), test_backtest_explains_when_the_period_is_shorter_than_the_window(), test_backtest_flags_var_that_was_too_low_or_too_high(), test_backtest_table_matches_var_backtest_for_the_chosen_window() (+8 more)

### Community 45 - "test_value_at_risk.py"
Cohesion: 0.07
Nodes (36): VaR models and backtesting, _validate_confidence(), _validate_dated_returns(), cornish_fisher_var(), _cornish_fisher_z(), kupiec_test(), normal_var(), rolling_var() (+28 more)

### Community 46 - "sortino_ratio"
Cohesion: 0.20
Nodes (13): calmar_ratio(), sortino_ratio(), dated(), test_analyze_portfolio_reports_sortino_and_calmar_on_its_daily_returns(), test_bigger_gains_raise_sortino_in_proportion_but_not_sharpe(), test_calmar_divides_compound_annual_growth_by_the_worst_drawdown(), test_calmar_is_nan_without_a_drawdown(), test_calmar_is_negative_when_the_portfolio_lost_money() (+5 more)

### Community 47 - "RiskLens Quant"
Cohesion: 0.14
Nodes (14): render_risk_sources(), Factor and sector exposure, Features, File structure, Historical VaR and CVaR, Holdings input, Installation, Risk-adjusted ratios (+6 more)

### Community 49 - "analyze_portfolio"
Cohesion: 0.29
Nodes (6): prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation(), test_rejects_invalid_inputs()

### Community 52 - "analytics/__init__.py"
Cohesion: 0.07
Nodes (21): Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), Rebalancing and trading costs, Rolling risk metrics, FactorExposure, BenchmarkStatistics, cumulative_wealth(), drawdown_series() (+13 more)

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 355 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `analytics/__init__.py` to `fetch_price_history`, `validation.py`, `simulate_portfolio`, `analyze_portfolio`, `efficient_frontier`, `test_concentration.py`, `historical_cvar`, `test_optimization.py`, `pytest`, `optimization.py`, `OptimizationError`, `fetch_prices`, `StressScenario`, `stress_test`, `portfolio_returns`, `estimate_inputs`, `pandas`, `test_holdings.py`, `test_metrics.py`, `test_engine_regression.py`, `data.py`, `test_value_at_risk.py`, `sortino_ratio`, `RiskLens Quant`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 65 inferred relationships involving `Analytics API` (e.g. with `factor_exposure()` and `FactorExposure`) actually correct?**
  _`Analytics API` has 65 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_concentration.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14492753623188406 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `simulate_portfolio` to `fetch_price_history`, `pandas`, `numpy`, `submit`, `app.py`, `analytics/__init__.py`, `test_simulation_memory.py`, `test_simulation.py`, `test_simulation_regression.py`, `simulation.py`, `simulation_memory.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_optimization.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10960960960960961 - nodes in this community are weakly interconnected._