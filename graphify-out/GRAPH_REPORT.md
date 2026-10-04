# Graph Report - RiskLens  (2026-11-01)

## Corpus Check
- 39 files · ~112,066 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 714 nodes · 2192 edges · 24 communities (21 shown, 3 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 366 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d5a4da34`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- test_validation.py
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
- validate_date_range
- test_metrics.py
- test_invalid_tail_data_hides_risk_results
- submit
- RiskLens Quant
- test_valid_stress_history_matches_backend_and_omits_missing_dates
- drawdown_series
- validation.py
- app.py
- click_button
- validate_weights

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 52 edges
2. `stress_test()` - 48 edges
3. `simulate_portfolio()` - 39 edges
4. `efficient_frontier()` - 34 edges
5. `five_assets()` - 32 edges
6. `analyze_portfolio()` - 29 edges
7. `custom_scenario()` - 25 edges
8. `min_volatility_portfolio()` - 24 edges
9. `to_returns()` - 24 edges
10. `max_sharpe_portfolio()` - 23 edges

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

## Communities (24 total, 3 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.09
Nodes (39): render_stress_test(), custom_scenario(), stress_test(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates(), test_early_history_end_allows_at_most_one_missing_weekday(), test_holiday_monday_end_with_friday_last_price_is_available() (+31 more)

### Community 1 - "test_validation.py"
Cohesion: 0.18
Nodes (12): validate_price_history(), validate_prices(), prices(), test_date_range_rejects_bad_input(), test_price_history_allows_an_asset_with_no_observations(), test_price_history_keeps_missing_values_without_mutating_input(), test_price_history_rejects_bad_input(), test_prices_honour_min_rows() (+4 more)

### Community 2 - "numpy"
Cohesion: 0.11
Nodes (32): _estimate_parameters(), simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day(), test_constant_growth_prices_give_exactly_zero_volatility() (+24 more)

### Community 3 - "data.py"
Cohesion: 0.10
Nodes (28): _close_prices(), DataFetchError, _download_close(), fetch_benchmark_prices(), fetch_price_history(), fetch_prices(), dates(), fetch() (+20 more)

### Community 4 - "test_smoke.py"
Cohesion: 0.15
Nodes (4): chart_values(), test_analyze_matches_engine_and_drawdown(), test_initial_dashboard_has_inputs_and_no_fake_results(), test_confidence_switch_uses_api_and_actual_histogram()

### Community 5 - "test_concentration.py"
Cohesion: 0.14
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.17
Nodes (16): analyzed_app(), make_prices(), prices(), select(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_least_risky_current_portfolio_has_no_same_risk_point(), test_negative_returns_keep_minimum_volatility_and_frontier() (+8 more)

### Community 7 - "pandas"
Cohesion: 0.14
Nodes (20): compare_to_benchmark(), _future_dates(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates(), test_both_curves_start_at_one_on_first_shared_date(), test_cumulative_wealth_compounds_from_one() (+12 more)

### Community 8 - "pytest"
Cohesion: 0.05
Nodes (35): Architecture, Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), Portfolio optimization, Rolling risk metrics, _aligned_returns(), benchmark_statistics(), BenchmarkStatistics (+27 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.06
Nodes (57): efficient_frontier(), EfficientFrontier, estimate_inputs(), frontier_point_within_risk(), max_sharpe_portfolio(), min_volatility_portfolio(), OptimizationError, _portfolio() (+49 more)

### Community 12 - "pytest"
Cohesion: 0.08
Nodes (43): _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility(), _validate_window() (+35 more)

### Community 13 - "validate_date_range"
Cohesion: 0.17
Nodes (8): _parse_date(), validate_date_range(), test_matching_time_zones_are_accepted(), test_missing_or_nonsense_start_is_rejected(), test_mixed_time_zones_raise_value_error(), test_today_is_a_valid_start_date(), test_tomorrow_is_rejected_as_future(), test_date_range_parses_strings_and_dates()

### Community 14 - "test_metrics.py"
Cohesion: 0.09
Nodes (32): historical_cvar(), historical_var(), tail_risk_summary(), _validate_confidence(), series(), test_annualized_return_and_volatility_use_252_days(), test_historical_var_is_negative_when_every_day_gains(), test_historical_var_is_positive_loss_at_confidence() (+24 more)

### Community 16 - "submit"
Cohesion: 0.08
Nodes (14): download(), prices(), submit(), test_constant_prices_show_undefined_sharpe(), test_failed_analysis_clears_previous_results(), test_historical_scenarios_use_their_own_download_window(), test_invalid_inputs_do_not_download(), test_new_analysis_resets_both_scenario_tools() (+6 more)

### Community 17 - "RiskLens Quant"
Cohesion: 0.12
Nodes (14): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR, Installation (+6 more)

### Community 18 - "test_valid_stress_history_matches_backend_and_omits_missing_dates"
Cohesion: 0.19
Nodes (5): app(), history(), test_late_listing_names_only_the_stock_with_insufficient_history(), test_stock_without_crisis_prices_has_an_accurate_unavailable_message(), test_valid_stress_history_matches_backend_and_omits_missing_dates()

### Community 19 - "drawdown_series"
Cohesion: 0.29
Nodes (7): drawdown_series(), dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates()

### Community 20 - "validation.py"
Cohesion: 0.29
Nodes (3): validate_tickers(), test_tickers_are_split_uppercased_and_deduplicated_in_order(), test_tickers_reject_bad_input()

### Community 21 - "app.py"
Cohesion: 0.13
Nodes (8): render_frontier(), render_optimization(), render_optimization_results(), render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_tail_risk()

### Community 22 - "click_button"
Cohesion: 0.29
Nodes (3): click_button(), test_custom_stress_metrics_chart_and_invalid_dates(), app_data()

### Community 23 - "validate_weights"
Cohesion: 0.33
Nodes (4): validate_weights(), test_weights_accept_ints_and_numpy_and_return_floats(), test_weights_allow_float_rounding_within_tolerance(), test_weights_reject_bad_input()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 210 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `pytest` to `stress_test`, `test_validation.py`, `numpy`, `data.py`, `test_concentration.py`, `pandas`, `test_optimization.py`, `pytest`, `validate_date_range`, `test_metrics.py`, `RiskLens Quant`, `drawdown_series`, `validation.py`, `validate_weights`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.0861952861952862 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `pandas`, `pytest`, `submit`, `RiskLens Quant`, `app.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Should `numpy` be split into smaller, more focused modules?**
  _Cohesion score 0.10815602836879433 - nodes in this community are weakly interconnected._