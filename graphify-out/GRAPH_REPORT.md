# Graph Report - RiskLens  (2026-11-01)

## Corpus Check
- 42 files · ~114,156 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 780 nodes · 2371 edges · 17 communities (14 shown, 3 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 376 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aba20610`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- test_validation.py
- numpy
- data.py
- pytest
- drawdown_series
- test_risk_ui.py
- pandas
- numpy
- risklens
- test_optimization.py
- pytest
- test_invalid_tail_data_hides_risk_results
- submit
- test_stress_history_ui.py
- app.py

## God Nodes (most connected - your core abstractions)
1. `stress_test()` - 53 edges
2. `Analytics API` - 52 edges
3. `simulate_portfolio()` - 45 edges
4. `efficient_frontier()` - 34 edges
5. `five_assets()` - 32 edges
6. `analyze_portfolio()` - 29 edges
7. `custom_scenario()` - 28 edges
8. `click_button()` - 26 edges
9. `min_volatility_portfolio()` - 24 edges
10. `to_returns()` - 24 edges

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

## Communities (17 total, 3 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.06
Nodes (45): render_stress_test(), _coverage_gaps(), custom_scenario(), _naive_dates(), _parse_date(), stress_test(), StressScenario, _weekdays_between() (+37 more)

### Community 1 - "test_validation.py"
Cohesion: 0.13
Nodes (16): validate_price_history(), validate_tickers(), prices(), test_date_range_rejects_bad_input(), test_price_history_allows_an_asset_with_no_observations(), test_price_history_keeps_missing_values_without_mutating_input(), test_price_history_rejects_bad_input(), test_prices_honour_min_rows() (+8 more)

### Community 2 - "numpy"
Cohesion: 0.05
Nodes (44): benchmark_returns(), main(), measure(), _estimate_parameters(), _future_dates(), simulate_portfolio(), _validate_int(), dated() (+36 more)

### Community 3 - "data.py"
Cohesion: 0.06
Nodes (43): Agent rules, AGENTS.md — RiskLens Quant, Architecture, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR (+35 more)

### Community 4 - "pytest"
Cohesion: 0.07
Nodes (40): correlation_matrix(), effective_holdings(), herfindahl_index(), historical_cvar(), tail_risk_summary(), test_concentration_accepts_numpy_weights_and_ignores_zero_weights(), test_concentration_rejects_invalid_weights(), test_constant_asset_has_nan_correlation() (+32 more)

### Community 5 - "drawdown_series"
Cohesion: 0.29
Nodes (7): drawdown_series(), dated(), test_does_not_mutate_input(), test_first_day_loss_counts_against_initial_wealth(), test_max_drawdown_is_minimum_of_series(), test_rejects_invalid_input(), test_tracks_peak_and_recovery_with_matching_dates()

### Community 6 - "test_risk_ui.py"
Cohesion: 0.17
Nodes (16): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_least_risky_current_portfolio_has_no_same_risk_point(), test_negative_returns_keep_minimum_volatility_and_frontier(), test_optimization_table_and_frontier_match_the_api() (+8 more)

### Community 7 - "pandas"
Cohesion: 0.10
Nodes (27): compare_to_benchmark(), _parse_date(), validate_date_range(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates(), test_both_curves_start_at_one_on_first_shared_date() (+19 more)

### Community 8 - "numpy"
Cohesion: 0.05
Nodes (43): Analytics API, Historical stress testing (`stress_test`, `run_stress_tests`), _aligned_returns(), benchmark_statistics(), BenchmarkStatistics, analyze_portfolio(), PortfolioMetrics, annualized_return() (+35 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.05
Nodes (62): render_frontier(), render_optimization(), render_optimization_results(), Portfolio optimization, efficient_frontier(), EfficientFrontier, estimate_inputs(), frontier_point_within_risk() (+54 more)

### Community 12 - "pytest"
Cohesion: 0.09
Nodes (38): Rolling risk metrics, _annualized_volatility(), _dated(), rolling_drawdown(), rolling_max_drawdown(), rolling_metrics(), rolling_sharpe(), rolling_volatility() (+30 more)

### Community 16 - "submit"
Cohesion: 0.06
Nodes (20): chart_values(), download(), prices(), submit(), test_analyze_matches_engine_and_drawdown(), test_constant_prices_show_undefined_sharpe(), test_custom_stress_metrics_chart_and_invalid_dates(), test_failed_analysis_clears_previous_results() (+12 more)

### Community 18 - "test_stress_history_ui.py"
Cohesion: 0.10
Nodes (21): select(), app(), history(), replay(), test_actual_price_dates_caption_counts_only_complete_returns(), test_custom_window_after_a_late_listing_replays_successfully(), test_delisted_stock_names_its_last_price_before_the_crisis_end(), test_download_problems_show_a_warning_and_keep_the_analysis() (+13 more)

### Community 19 - "app.py"
Cohesion: 0.15
Nodes (5): render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_tail_risk()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 240 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `numpy` to `stress_test`, `test_validation.py`, `numpy`, `data.py`, `pytest`, `drawdown_series`, `pandas`, `test_optimization.py`, `pytest`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 37 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.06012176560121765 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `data.py`, `pandas`, `numpy`, `submit`, `app.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_validation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._