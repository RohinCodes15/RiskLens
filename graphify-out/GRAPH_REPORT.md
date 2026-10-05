# Graph Report - RiskLens  (2026-11-01)

## Corpus Check
- 39 files · ~113,006 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 744 nodes · 2284 edges · 24 communities (21 shown, 3 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 370 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f4c15f74`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- test_validation.py
- numpy
- test_data.py
- test_concentration.py
- stress_test
- test_risk_ui.py
- pandas
- test_metrics.py
- risklens
- test_optimization.py
- pytest
- optimization.py
- data.py
- test_invalid_tail_data_hides_risk_results
- submit
- analyze_portfolio
- test_stress_history_ui.py
- app.py
- Analytics API
- analytics/__init__.py
- RiskLens Quant
- test_stress_history.py

## God Nodes (most connected - your core abstractions)
1. `Analytics API` - 52 edges
2. `stress_test()` - 51 edges
3. `simulate_portfolio()` - 39 edges
4. `efficient_frontier()` - 34 edges
5. `five_assets()` - 32 edges
6. `analyze_portfolio()` - 29 edges
7. `custom_scenario()` - 26 edges
8. `click_button()` - 26 edges
9. `min_volatility_portfolio()` - 24 edges
10. `to_returns()` - 24 edges

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
Cohesion: 0.08
Nodes (29): custom_scenario(), _parse_date(), _weekdays_between(), prices(), test_different_asset_calendars_use_only_common_actual_prices(), test_documented_scenarios_have_expected_peak_to_trough_dates(), test_early_history_end_allows_at_most_one_missing_weekday(), test_holiday_monday_end_with_friday_last_price_is_available() (+21 more)

### Community 1 - "test_validation.py"
Cohesion: 0.12
Nodes (18): validate_tickers(), validate_weights(), prices(), test_date_range_parses_strings_and_dates(), test_date_range_rejects_bad_input(), test_price_history_allows_an_asset_with_no_observations(), test_price_history_keeps_missing_values_without_mutating_input(), test_price_history_rejects_bad_input() (+10 more)

### Community 2 - "numpy"
Cohesion: 0.10
Nodes (33): _estimate_parameters(), _future_dates(), simulate_portfolio(), _validate_int(), dated(), noisy(), test_bad_settings_raise_value_error(), test_close_stamped_history_keeps_time_of_day() (+25 more)

### Community 3 - "test_data.py"
Cohesion: 0.18
Nodes (20): dates(), fetch(), history(), test_bad_date_range_is_rejected_before_download(), test_drops_dates_missing_for_any_ticker(), test_empty_ticker_list_is_rejected_before_download(), test_flat_single_ticker_response_is_named_after_ticker(), test_malformed_or_invalid_responses_raise_data_fetch_error() (+12 more)

### Community 4 - "test_concentration.py"
Cohesion: 0.14
Nodes (15): correlation_matrix(), effective_holdings(), herfindahl_index(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation(), test_correlation_drops_rows_with_missing_returns(), test_correlation_matrix_is_symmetric_with_unit_diagonal() (+7 more)

### Community 5 - "stress_test"
Cohesion: 0.18
Nodes (9): Historical stress testing (`stress_test`, `run_stress_tests`), max_drawdown(), _coverage_gaps(), _naive_dates(), run_stress_tests(), stress_test(), StressResult, StressScenario (+1 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.17
Nodes (16): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_least_risky_current_portfolio_has_no_same_risk_point(), test_negative_returns_keep_minimum_volatility_and_frontier(), test_optimization_table_and_frontier_match_the_api() (+8 more)

### Community 7 - "pandas"
Cohesion: 0.09
Nodes (28): _aligned_returns(), benchmark_statistics(), compare_to_benchmark(), _parse_date(), validate_date_range(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta() (+20 more)

### Community 8 - "test_metrics.py"
Cohesion: 0.07
Nodes (40): annualized_return(), _as_float_values(), historical_cvar(), historical_var(), risk_contributions(), sharpe_ratio(), tail_risk_summary(), _validate_confidence() (+32 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.05
Nodes (62): render_frontier(), render_optimization(), render_optimization_results(), Portfolio optimization, efficient_frontier(), EfficientFrontier, estimate_inputs(), frontier_point_within_risk() (+54 more)

### Community 12 - "pytest"
Cohesion: 0.07
Nodes (45): Rolling risk metrics, drawdown_series(), _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe() (+37 more)

### Community 13 - "optimization.py"
Cohesion: 0.15
Nodes (4): SolverDiagnostics, validate_price_history(), validate_prices(), validate_risk_free_rate()

### Community 14 - "data.py"
Cohesion: 0.18
Nodes (8): _close_prices(), DataFetchError, _download_close(), fetch_benchmark_prices(), fetch_price_history(), fetch_prices(), test_download_exception_becomes_data_fetch_error(), test_price_history_download_exception_becomes_data_fetch_error()

### Community 16 - "submit"
Cohesion: 0.06
Nodes (20): chart_values(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results() (+12 more)

### Community 17 - "analyze_portfolio"
Cohesion: 0.29
Nodes (6): prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation(), test_rejects_invalid_inputs()

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.09
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.15
Nodes (6): render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_stress_test(), render_tail_risk()

### Community 20 - "Analytics API"
Cohesion: 0.22
Nodes (7): Architecture, Analytics API, BenchmarkStatistics, analyze_portfolio(), PortfolioMetrics, portfolio_returns(), to_returns()

### Community 21 - "analytics/__init__.py"
Cohesion: 0.20
Nodes (3): annualized_volatility(), cumulative_wealth(), MonteCarloResult

### Community 22 - "RiskLens Quant"
Cohesion: 0.12
Nodes (14): Agent rules, AGENTS.md — RiskLens Quant, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR, Installation (+6 more)

### Community 23 - "test_stress_history.py"
Cohesion: 0.32
Nodes (10): history(), test_common_dates_hid_which_asset_listed_late(), test_custom_window_after_listing_is_available(), test_delisted_ticker_reports_the_scenario_end(), test_every_scenario_names_only_the_late_listing(), test_fully_covered_portfolio_matches_common_date_results(), test_missing_day_inside_window_is_dropped_not_reported(), test_recent_ipo_is_the_only_asset_blamed() (+2 more)

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 225 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `Analytics API` to `stress_test`, `test_validation.py`, `numpy`, `test_concentration.py`, `stress_test`, `pandas`, `test_metrics.py`, `test_optimization.py`, `pytest`, `optimization.py`, `data.py`, `analytics/__init__.py`, `RiskLens Quant`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.08139534883720931 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `pandas`, `submit`, `app.py`, `Analytics API`, `analytics/__init__.py`, `RiskLens Quant`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_validation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11692307692307692 - nodes in this community are weakly interconnected._