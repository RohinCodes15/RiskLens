"""Network-free rolling-risk and risk-attribution dashboard checks using the real analytics API."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import APP_PATH, chart_spec, chart_values, click_button

from risklens.analytics import (
    OptimizationError,
    analyze_portfolio,
    efficient_frontier,
    frontier_point_within_risk,
    max_sharpe_portfolio,
    min_volatility_portfolio,
    risk_contributions,
    rolling_metrics,
)
from risklens.data import to_returns


def make_prices(periods: int = 150) -> pd.DataFrame:
    """Seeded adjusted prices for three loosely related stocks."""
    daily = np.random.default_rng(3).normal([4e-4, 6e-4, 2e-4], [0.012, 0.02, 0.008], (periods, 3))
    return pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        columns=["AAPL", "MSFT", "KO"],
        index=pd.bdate_range("2025-01-02", periods=periods),
    )


def analyzed_app(prices: pd.DataFrame, tickers: str = "AAPL, MSFT, KO") -> AppTest:
    """Run the dashboard on mocked prices with equal default weights."""
    with patch("yfinance.download", return_value=pd.concat({"Close": prices}, axis=1)):
        app = AppTest.from_file(APP_PATH).run()
        app.text_input[0].set_value(tickers).run()
        return click_button(app, "Analyze portfolio")


def select(app: AppTest, label: str, value: object) -> AppTest:
    return next(widget for widget in app.selectbox if widget.label == label).select(value).run()


@pytest.fixture
def prices() -> pd.DataFrame:
    return make_prices()


# --- rolling risk ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("window", "view", "column"),
    [
        (21, "Volatility", "volatility"),
        (63, "Sharpe ratio", "sharpe"),
        (126, "Drawdown", "drawdown"),
    ],
)
def test_rolling_chart_matches_the_api(
    prices: pd.DataFrame, window: int, view: str, column: str
) -> None:
    app = analyzed_app(prices)
    select(app, "Rolling window", window)
    select(app, "Rolling metric", view)
    assert not app.exception and not app.error
    weights = app.session_state["analysis"]["weights"]
    expected = rolling_metrics(analyze_portfolio(prices, weights).daily_returns, window)[
        column
    ].dropna()
    trace = chart_spec(app, "rolling_chart")["data"][0]
    np.testing.assert_allclose(chart_values(trace["y"]), expected.to_numpy())
    assert pd.to_datetime(trace["x"]).tolist() == expected.index.tolist()


def test_rolling_window_longer_than_history_shows_guidance() -> None:
    app = analyzed_app(make_prices(periods=30))
    select(app, "Rolling window", 63)
    assert not app.exception and not app.error
    assert not any(chart.key == "rolling_chart" for chart in app.get("plotly_chart"))
    assert any("63-day window needs at least 63 daily returns" in note.value for note in app.info)


# --- risk attribution -----------------------------------------------------------------


def test_risk_attribution_chart_matches_weights_and_api(prices: pd.DataFrame) -> None:
    app = analyzed_app(prices)
    assert not app.exception and not app.error
    weights = app.session_state["analysis"]["weights"]
    allocation, risk = chart_spec(app, "risk_attribution_chart")["data"]
    np.testing.assert_allclose(chart_values(allocation["y"]), weights)
    expected = risk_contributions(to_returns(prices), weights)
    np.testing.assert_allclose(chart_values(risk["y"]), expected.to_numpy())
    assert np.isclose(chart_values(risk["y"]).sum(), 1.0)


def test_constant_prices_show_attribution_unavailable(prices: pd.DataFrame) -> None:
    app = analyzed_app(prices * 0 + 100.0)
    assert not app.exception
    assert not any(chart.key == "risk_attribution_chart" for chart in app.get("plotly_chart"))
    assert any("Risk attribution is unavailable" in note.value for note in app.info)


# --- optimization and efficient frontier -------------------------------------------------


def test_optimization_waits_for_the_button(prices: pd.DataFrame) -> None:
    with patch("risklens.analytics.efficient_frontier") as frontier:
        app = analyzed_app(prices)
    frontier.assert_not_called()
    assert not app.dataframe
    assert any("Select Optimize portfolio" in note.value for note in app.info)


def test_optimization_table_and_frontier_match_the_api(prices: pd.DataFrame) -> None:
    app = click_button(analyzed_app(prices), "Optimize portfolio")
    assert not app.exception and not app.error
    analysis = app.session_state["analysis"]
    current = analyze_portfolio(prices, analysis["weights"])
    min_vol, max_sharpe = min_volatility_portfolio(prices), max_sharpe_portfolio(prices)
    table = app.dataframe[0].value
    np.testing.assert_allclose(table["Minimum volatility"].iloc[:3], min_vol.weights, atol=1e-6)
    np.testing.assert_allclose(table["Maximum Sharpe"].iloc[:3], max_sharpe.weights, atol=1e-6)
    assert np.isclose(table.loc["Annualized volatility", "Current"], current.annualized_volatility)

    frontier = efficient_frontier(prices)
    traces = {trace["name"]: trace for trace in chart_spec(app, "frontier_chart")["data"]}
    np.testing.assert_allclose(
        chart_values(traces["Efficient frontier"]["x"]), frontier.points["volatility"], rtol=1e-6
    )
    assert np.isclose(chart_values(traces["Current"]["x"])[0], current.annualized_volatility)
    best = frontier.points.loc[frontier_point_within_risk(frontier, current.annualized_volatility)]
    assert np.isclose(
        chart_values(traces["Best return at your risk"]["y"])[0], best["expected_return"], rtol=1e-6
    )
    assert best["volatility"] <= current.annualized_volatility + 1e-6


def test_least_risky_current_portfolio_has_no_same_risk_point(prices: pd.DataFrame) -> None:
    with patch("risklens.analytics.frontier_point_within_risk", return_value=None):
        app = click_button(analyzed_app(prices), "Optimize portfolio")
    assert not app.exception
    names = [trace["name"] for trace in chart_spec(app, "frontier_chart")["data"]]
    assert "Best return at your risk" not in names
    assert any("no same-risk alternative" in note.value for note in app.info)


@pytest.mark.parametrize(
    ("optimizer", "missing_column", "has_frontier"),
    [
        ("min_volatility_portfolio", "Minimum volatility", True),
        ("max_sharpe_portfolio", "Maximum Sharpe", True),
        ("efficient_frontier", None, False),
    ],
)
def test_optimizer_failure_shows_a_warning(
    prices: pd.DataFrame, optimizer: str, missing_column: str | None, has_frontier: bool
) -> None:
    error = OptimizationError("Solver did not converge.")
    with patch(f"risklens.analytics.{optimizer}", side_effect=error):
        app = click_button(analyzed_app(prices), "Optimize portfolio")
    assert not app.exception and not app.error
    assert any("Solver did not converge" in note.value for note in app.warning)
    columns = app.dataframe[0].value.columns
    assert "Current" in columns
    for label in ["Minimum volatility", "Maximum Sharpe"]:
        assert (label in columns) == (label != missing_column)
    assert any(chart.key == "frontier_chart" for chart in app.get("plotly_chart")) == has_frontier
    if has_frontier:
        names = [trace["name"] for trace in chart_spec(app, "frontier_chart")["data"]]
        assert missing_column not in names
        assert "Current" in names and "Efficient frontier" in names


def test_negative_returns_keep_minimum_volatility_and_frontier() -> None:
    """Undefined maximum Sharpe must not hide valid lower-risk allocations."""
    daily = np.random.default_rng(11).uniform(-0.02, -0.001, (80, 3))
    prices = pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        columns=["AAPL", "MSFT", "KO"],
        index=pd.bdate_range("2025-01-02", periods=80),
    )
    app = click_button(analyzed_app(prices), "Optimize portfolio")
    assert not app.exception and not app.error
    assert any(
        "Maximum Sharpe" in note.value and "risk-free rate" in note.value for note in app.warning
    )
    table = app.dataframe[0].value
    assert list(table.columns) == ["Current", "Minimum volatility"]
    expected = min_volatility_portfolio(prices)
    np.testing.assert_allclose(table["Minimum volatility"].iloc[:3], expected.weights)
    frontier = efficient_frontier(prices)
    traces = {trace["name"]: trace for trace in chart_spec(app, "frontier_chart")["data"]}
    assert "Maximum Sharpe" not in traces and "Minimum volatility" in traces
    np.testing.assert_allclose(
        chart_values(traces["Efficient frontier"]["y"]), frontier.points["expected_return"]
    )


def test_failed_optimization_rerun_clears_stale_results_and_recovers(prices: pd.DataFrame) -> None:
    """Failed reruns remove obsolete outputs; a later success clears all warnings."""
    app = click_button(analyzed_app(prices), "Optimize portfolio")
    error = OptimizationError("Solver did not converge.")
    with (
        patch("risklens.analytics.min_volatility_portfolio", side_effect=error),
        patch("risklens.analytics.max_sharpe_portfolio", side_effect=error),
        patch("risklens.analytics.efficient_frontier", side_effect=error),
    ):
        click_button(app, "Optimize portfolio")
    assert not app.exception and not app.error
    assert not app.dataframe
    assert "frontier_chart" not in [chart.key for chart in app.get("plotly_chart")]
    assert sum("Solver did not converge" in note.value for note in app.warning) == 3
    app.run()
    assert sum("Solver did not converge" in note.value for note in app.warning) == 3
    click_button(app, "Optimize portfolio")
    assert not app.exception and not app.error
    assert "Maximum Sharpe" in app.dataframe[0].value.columns
    assert chart_spec(app, "frontier_chart")["data"]
    assert not any("Solver did not converge" in note.value for note in app.warning)


def test_single_stock_skips_optimization(prices: pd.DataFrame) -> None:
    app = analyzed_app(prices[["AAPL"]], tickers="AAPL")
    assert not app.exception
    assert not any(button.label == "Optimize portfolio" for button in app.button)
    assert any("at least two stocks" in note.value for note in app.info)


def test_frontier_reuses_the_minimum_volatility_result(prices: pd.DataFrame) -> None:
    with patch("risklens.analytics.efficient_frontier", wraps=efficient_frontier) as frontier:
        app = click_button(analyzed_app(prices), "Optimize portfolio")
    assert not app.exception and not app.error
    min_vol = app.session_state["analysis"]["optimization"][0]
    assert frontier.call_count == 1
    assert frontier.call_args.kwargs["min_volatility"] is min_vol
