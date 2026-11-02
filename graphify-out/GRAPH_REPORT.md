# Graph Report - RiskLens  (2026-11-02)

## Corpus Check
- 42 files · ~114,696 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 797 nodes · 2436 edges · 20 communities (18 shown, 2 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 398 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `57c1186a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- stress_test
- pytest
- numpy
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
- five_assets
- OptimizationError
- submit
- EfficientFrontier
- test_stress_history_ui.py
- app.py

## God Nodes (most connected - your core abstractions)
1. `stress_test()` - 53 edges
2. `Analytics API` - 52 edges
3. `efficient_frontier()` - 47 edges
4. `simulate_portfolio()` - 45 edges
5. `five_assets()` - 40 edges
6. `analyze_portfolio()` - 29 edges
7. `min_volatility_portfolio()` - 28 edges
8. `custom_scenario()` - 28 edges
9. `click_button()` - 28 edges
10. `max_sharpe_portfolio()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Historical VaR and CVaR` --references--> `tail_risk_summary()`  [INFERRED]
  README.md → src/risklens/analytics/metrics.py
- `Monte Carlo (`simulate_portfolio`)` --references--> `simulate_portfolio()`  [INFERRED]
  README.md → src/risklens/analytics/simulation.py
- `Analytics API` --references--> `compare_to_benchmark()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py
- `Analytics API` --references--> `benchmark_statistics()`  [INFERRED]
  README.md → src/risklens/analytics/benchmark.py
- `Analytics API` --references--> `herfindahl_index()`  [INFERRED]
  README.md → src/risklens/analytics/concentration.py

## Import Cycles
- None detected.

## Communities (20 total, 2 thin omitted)

### Community 0 - "stress_test"
Cohesion: 0.05
Nodes (50): render_stress_test(), Historical stress testing (`stress_test`, `run_stress_tests`), cumulative_wealth(), _coverage_gaps(), custom_scenario(), _naive_dates(), _parse_date(), run_stress_tests() (+42 more)

### Community 1 - "pytest"
Cohesion: 0.05
Nodes (43): correlation_matrix(), effective_holdings(), herfindahl_index(), _parse_date(), validate_date_range(), validate_price_history(), validate_prices(), validate_risk_free_rate() (+35 more)

### Community 2 - "numpy"
Cohesion: 0.05
Nodes (45): benchmark_returns(), main(), measure(), _estimate_parameters(), _future_dates(), MonteCarloResult, simulate_portfolio(), _validate_int() (+37 more)

### Community 3 - "data.py"
Cohesion: 0.06
Nodes (44): Agent rules, AGENTS.md — RiskLens Quant, Architecture, Coding standards, Ownership, Features, File structure, Historical VaR and CVaR (+36 more)

### Community 4 - "analyze_portfolio"
Cohesion: 0.26
Nodes (7): analyze_portfolio(), prices(), test_constant_prices_give_zero_rates_and_nan_sharpe(), test_does_not_mutate_prices(), test_first_day_loss_counts_in_max_drawdown(), test_metrics_match_hand_calculation(), test_rejects_invalid_inputs()

### Community 5 - "efficient_frontier"
Cohesion: 0.15
Nodes (22): efficient_frontier(), frontier_point_within_risk(), min_volatility_portfolio(), test_frontier_has_requested_points_in_increasing_return_order(), test_frontier_weights_are_long_only_and_metrics_match_engine(), test_invalid_point_counts_are_rejected(), test_invalid_risk_free_rate_is_rejected(), test_reused_min_volatility_gives_the_same_frontier() (+14 more)

### Community 6 - "test_risk_ui.py"
Cohesion: 0.16
Nodes (18): analyzed_app(), make_prices(), prices(), test_constant_prices_show_attribution_unavailable(), test_failed_optimization_rerun_clears_stale_results_and_recovers(), test_frontier_reuses_the_minimum_volatility_result(), test_frontier_solves_its_own_minimum_volatility_after_a_failure(), test_least_risky_current_portfolio_has_no_same_risk_point() (+10 more)

### Community 7 - "pandas"
Cohesion: 0.10
Nodes (24): _aligned_returns(), benchmark_statistics(), compare_to_benchmark(), series_from_returns(), test_constant_benchmark_returns_are_rejected(), test_low_volatility_benchmark_still_gives_beta(), dates(), test_both_curves_start_at_one_on_first_shared_date() (+16 more)

### Community 8 - "metrics.py"
Cohesion: 0.06
Nodes (42): annualized_return(), annualized_volatility(), _as_float_values(), historical_cvar(), historical_var(), portfolio_returns(), risk_contributions(), sharpe_ratio() (+34 more)

### Community 11 - "test_optimization.py"
Cohesion: 0.17
Nodes (19): estimate_inputs(), max_sharpe_portfolio(), test_equal_expected_returns_give_the_single_min_volatility_point(), test_frontier_runs_from_min_volatility_to_best_single_asset(), make_prices(), test_constant_price_asset_gives_zero_volatility_and_nan_sharpe(), test_duplicate_asset_is_flagged_singular_but_still_solved(), test_estimate_inputs_annualizes_mean_and_sample_covariance() (+11 more)

### Community 12 - "pytest"
Cohesion: 0.06
Nodes (50): Analytics API, Rolling risk metrics, BenchmarkStatistics, PortfolioMetrics, drawdown_series(), max_drawdown(), SolverDiagnostics, _annualized_volatility() (+42 more)

### Community 13 - "optimization.py"
Cohesion: 0.12
Nodes (8): Portfolio optimization, _min_volatility(), OptimizedPortfolio, _portfolio(), _reused_min_volatility_return(), _solve(), _target_return_solve(), _validate_points()

### Community 14 - "five_assets"
Cohesion: 0.16
Nodes (13): test_no_sampled_portfolio_beats_a_frontier_point(), five_assets(), random_portfolios(), test_diagnostics_report_a_converged_full_rank_solve(), test_infeasible_solver_output_raises_optimization_error(), test_invalid_prices_are_rejected(), test_invalid_risk_free_rate_is_rejected(), test_max_sharpe_is_not_beaten_by_any_sampled_portfolio() (+5 more)

### Community 15 - "OptimizationError"
Cohesion: 0.24
Nodes (7): OptimizationError, test_frontier_estimates_inputs_and_solves_min_volatility_once(), test_frontier_with_no_solvable_point_raises(), always_fails(), test_infeasible_targets_are_dropped_and_counted(), every_third_fails(), test_optimization_error_is_a_value_error()

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
Cohesion: 0.17
Nodes (5): render_risk_attribution(), render_rolling(), render_simulation(), render_stress_result(), render_tail_risk()

## Knowledge Gaps
- **1 isolated node(s):** `risklens`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 244 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Analytics API` connect `pytest` to `stress_test`, `pytest`, `numpy`, `data.py`, `analyze_portfolio`, `efficient_frontier`, `pandas`, `metrics.py`, `test_optimization.py`, `optimization.py`, `OptimizationError`, `EfficientFrontier`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `stress_test()` (e.g. with `Architecture` and `render_stress_test()`) actually correct?**
  _`stress_test()` has 37 INFERRED edges - model-reasoned connections that need verification._
- **What connects `risklens` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `stress_test` be split into smaller, more focused modules?**
  _Cohesion score 0.05225718194254446 - nodes in this community are weakly interconnected._
- **Why does `simulate_portfolio()` connect `numpy` to `data.py`, `pandas`, `pytest`, `submit`, `app.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `Analytics API` (e.g. with `benchmark_statistics()` and `BenchmarkStatistics`) actually correct?**
  _`Analytics API` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Should `pytest` be split into smaller, more focused modules?**
  _Cohesion score 0.05263157894736842 - nodes in this community are weakly interconnected._