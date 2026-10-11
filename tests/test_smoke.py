"""Network-free dashboard checks using mocked downloads and the analytics API."""

import base64
import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import (
    HISTORICAL_SCENARIOS,
    analyze_portfolio,
    compare_to_benchmark,
    cumulative_wealth,
    custom_scenario,
    drawdown_series,
    effective_holdings,
    herfindahl_index,
    portfolio_returns,
    simulate_portfolio,
    stress_test,
)
from risklens.data import to_returns

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def prices() -> pd.DataFrame:
    """Adjusted daily prices with both gains and losses, in quoted currency."""
    return pd.DataFrame(
        {"AAPL": [100.0, 90.0, 108.0, 105.0], "MSFT": [200.0, 210.0, 189.0, 205.0]},
        index=pd.bdate_range("2026-01-05", periods=4, name="Date"),
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    """Prevent every dashboard test from accessing Yahoo Finance."""
    with patch("yfinance.download", return_value=pd.concat({"Close": prices}, axis=1)) as mock:
        yield mock


def submit(app: AppTest) -> AppTest:
    """Submit the dashboard with a fixed historical period (inclusive end)."""
    app.date_input[0].set_value(date(2026, 1, 1))
    app.date_input[1].set_value(date(2026, 1, 10))
    return app.button[0].click().run()


def chart_values(values: list[float] | dict[str, str]) -> np.ndarray:
    """Decode Plotly JSON values as daily drawdown fractions."""
    if isinstance(values, dict):
        return np.frombuffer(base64.b64decode(values["bdata"]), dtype=values["dtype"])
    return np.asarray(values)


def test_initial_dashboard_has_inputs_and_no_fake_results(download: MagicMock) -> None:
    """Initial UI has percentage weights and no calculated cards or charts."""
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert any(title.value == "RiskLens Quant" for title in app.title)
    assert app.text_input[0].value == "AAPL, MSFT"
    assert [widget.value for widget in app.number_input] == [50.0, 50.0]
    assert len(app.date_input) == 2
    assert not app.metric and not app.get("plotly_chart")
    assert any("not investment advice" in caption.value for caption in app.caption)
    download.assert_not_called()


def test_analyze_matches_engine_and_drawdown(prices: pd.DataFrame, download: MagicMock) -> None:
    """Cards and dated drawdown match the real engine for 60/40 weights."""
    expected = analyze_portfolio(prices, [0.6, 0.4])
    with patch("risklens.analytics.analyze_portfolio", wraps=analyze_portfolio) as engine:
        app = AppTest.from_file(APP_PATH).run()
        app.number_input[0].set_value(60.0)
        app.number_input[1].set_value(40.0)
        submit(app)
        assert not app.exception and not app.error
        assert [card.label for card in app.metric][:6] == [
            "Annualized return", "Annualized volatility", "Sharpe ratio", "Maximum drawdown",
            "HHI concentration", "Effective number of holdings",
        ]
        assert [card.value for card in app.metric][:6] == [
            f"{expected.annualized_return:.2%}", f"{expected.annualized_volatility:.2%}",
            f"{expected.sharpe_ratio:.2f}", f"{expected.max_drawdown:.2%}",
            f"{herfindahl_index([0.6, 0.4]):.3f}", f"{effective_holdings([0.6, 0.4]):.2f}",
        ]
        pd.testing.assert_frame_equal(engine.call_args.args[0], prices)
        np.testing.assert_allclose(engine.call_args.args[1], [0.6, 0.4])
        assert download.call_args.kwargs["end"] == date(2026, 1, 11)
        assert download.call_args.kwargs["auto_adjust"] is True
        charts = app.get("plotly_chart")
        assert len(charts) == 4
        figure = json.loads(charts[1].proto.spec)
        trace = figure["data"][0]
        expected_drawdown = drawdown_series(expected.daily_returns)
        np.testing.assert_allclose(chart_values(trace["y"]), expected_drawdown.to_numpy())
        assert pd.to_datetime(trace["x"]).tolist() == expected_drawdown.index.tolist()
        assert trace["fill"] == "tozeroy"
        assert figure["layout"]["yaxis"]["tickformat"] == ".0%"
        assert figure["layout"]["xaxis"]["rangeslider"]["visible"] is True
        app.checkbox[0].uncheck().run()
        assert json.loads(app.get("plotly_chart")[1].proto.spec)["layout"]["xaxis"]["rangeslider"]["visible"] is False
        engine.assert_called_once()


@pytest.mark.parametrize("invalid", ["tickers", "weights", "dates"])
def test_invalid_inputs_do_not_download(invalid: str, download: MagicMock) -> None:
    """Bad ticker symbols, percentage totals, and dates show friendly errors."""
    app = AppTest.from_file(APP_PATH).run()
    if invalid == "tickers":
        app.text_input[0].set_value("???").run()
        assert app.button[0].disabled
    else:
        if invalid == "weights":
            app.number_input[0].set_value(25.0)
        else:
            app.date_input[0].set_value(date(2026, 1, 10))
            app.date_input[1].set_value(date(2026, 1, 1))
        app.button[0].click().run()
    assert not app.exception and app.error
    assert not app.metric and not app.get("plotly_chart")
    download.assert_not_called()


@pytest.mark.parametrize("failure", ["empty", "network", "analytics", "unfinished"])
def test_failed_analysis_clears_previous_results(
    failure: str, prices: pd.DataFrame, download: MagicMock,
) -> None:
    """Failed requests clear old results and show an error instead of crashing."""
    app = AppTest.from_file(APP_PATH).run()
    app.session_state["analysis"] = {
        "prices": prices, "weights": [0.5, 0.5],
        "metrics": (0.1, 0.2, 0.5, -0.1),
        "drawdown": pd.Series([0.0, -0.1], index=prices.index[:2]),
    }
    if failure == "empty":
        download.return_value = pd.DataFrame()
    elif failure == "network":
        download.side_effect = RuntimeError("Download unavailable")
    engine_error = NotImplementedError("Unfinished") if failure == "unfinished" else ValueError("Invalid price history")
    with patch("risklens.analytics.analyze_portfolio", side_effect=engine_error):
        submit(app)
    assert not app.exception and app.error
    assert "analysis" not in app.session_state
    assert not app.metric and not app.get("plotly_chart")
    if failure == "unfinished":
        assert "analytics is not ready" in app.error[0].value


def test_constant_prices_show_undefined_sharpe(download: MagicMock, prices: pd.DataFrame) -> None:
    """A flat portfolio shows real zero rates and an undefined Sharpe ratio."""
    download.return_value = pd.concat({"Close": prices * 0 + 100.0}, axis=1)
    app = AppTest.from_file(APP_PATH).run()
    submit(app)
    assert not app.exception and not app.error
    assert [card.value for card in app.metric][:6] == ["0.00%", "0.00%", "N/A", "0.00%", "0.500", "2.00"]
    assert len(app.get("plotly_chart")) == 4
    assert any("undefined correlation" in note.value for note in app.info)


def test_single_stock_shows_full_concentration_without_heatmap(
    download: MagicMock, prices: pd.DataFrame,
) -> None:
    """One holding is fully concentrated and has no correlation heatmap."""
    download.return_value = pd.concat({"Close": prices[["AAPL"]]}, axis=1)
    app = AppTest.from_file(APP_PATH).run()
    app.text_input[0].set_value("AAPL").run()
    submit(app)
    assert not app.exception and not app.error
    assert [card.value for card in app.metric][4:6] == ["1.000", "1.00"]
    assert "correlation_heatmap" not in [chart.key for chart in app.get("plotly_chart")]
    assert any("single-stock portfolio" in note.value for note in app.info)


def test_spy_comparison_shows_chart_and_ending_returns(
    download: MagicMock, prices: pd.DataFrame,
) -> None:
    """With SPY available, the chart and cards match the date-aligned API."""
    spy = pd.Series([500.0, 505.0, 495.0, 510.0], index=prices.index, name="SPY")

    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        frame = spy.to_frame() if list(tickers) == ["SPY"] else prices
        return pd.concat({"Close": frame}, axis=1)

    download.side_effect = fake_download
    expected = compare_to_benchmark(prices, [0.5, 0.5], spy).iloc[-1] - 1.0
    app = submit(AppTest.from_file(APP_PATH).run())
    assert not app.exception and not app.error
    assert not any("Benchmark comparison is unavailable" in note.value for note in app.warning)
    assert "benchmark_chart" in [chart.key for chart in app.get("plotly_chart")]
    assert [(card.label, card.value) for card in app.metric if card.label in {"Portfolio ending return", "SPY ending return"}] == [
        ("Portfolio ending return", f"{expected['portfolio']:.2%}"),
        ("SPY ending return", f"{expected['benchmark']:.2%}"),
    ]
    assert expected["benchmark"] == pytest.approx(0.02)


def test_spy_failure_keeps_portfolio_results(download: MagicMock) -> None:
    """A missing SPY download warns without hiding the portfolio analysis."""
    app = submit(AppTest.from_file(APP_PATH).run())
    assert not app.exception and not app.error
    assert any("Benchmark comparison is unavailable" in note.value for note in app.warning)
    assert "benchmark_chart" not in [chart.key for chart in app.get("plotly_chart")]
    assert [card.label for card in app.metric][0] == "Annualized return"


def click_button(app: AppTest, label: str) -> AppTest:
    """Click a named action independently of sidebar/widget ordering."""
    return next(button for button in app.button if button.label == label).click().run()


def chart_spec(app: AppTest, key: str) -> dict:
    """Read a named Plotly figure without relying on section order."""
    return json.loads(next(chart for chart in app.get("plotly_chart") if chart.key == key).proto.spec)


def test_simulation_controls_fan_and_persistence(prices: pd.DataFrame, download: MagicMock) -> None:
    """Settings reach the real engine; every band and card matches its outputs."""
    with patch("risklens.analytics.simulate_portfolio", wraps=simulate_portfolio) as engine:
        app = submit(AppTest.from_file(APP_PATH).run())
        assert [tab.label for tab in app.tabs] == ["Simulated futures", "Historical scenarios"]
        for label, value in [("Forecast horizon (trading days)", 10), ("Simulation count", 2000), ("Random seed", 7)]:
            next(widget for widget in app.number_input if widget.label == label).set_value(value)
        engine.assert_not_called()
        click_button(app, "Run hypothetical simulations")
        assert not app.exception and not app.error
        expected = simulate_portfolio(analyze_portfolio(prices, [0.5, 0.5]).daily_returns, 10, 2000, 7)
        assert engine.call_args.kwargs == {"horizon_days": 10, "n_paths": 2000, "seed": 7}
        pd.testing.assert_series_equal(engine.call_args.args[0], analyze_portfolio(prices, [0.5, 0.5]).daily_returns)
        figure = chart_spec(app, "simulation_chart")
        assert len(figure["data"]) == 5
        for trace, column in zip(figure["data"], ["p5", "p95", "p25", "p75", "median"], strict=True):
            np.testing.assert_allclose(chart_values(trace["y"]), expected.percentile_paths[column])
            assert pd.to_datetime(trace["x"]).tolist() == expected.percentile_paths.index.tolist()
        assert [figure["data"][i]["fill"] for i in [1, 3]] == ["tonexty", "tonexty"]
        cards = {card.label: card.value for card in app.metric}
        assert cards["Hypothetical terminal median return"] == f"{expected.percentile_paths['median'].iloc[-1] - 1:.2%}"
        assert cards["Hypothetical probability of loss"] == f"{expected.loss_probability:.2%}"
        assert any("not predictions" in caption.value for caption in app.caption)
        calls = download.call_count
        app.checkbox[0].uncheck().run()
        engine.assert_called_once()
        assert download.call_count == calls


@pytest.mark.parametrize("failure", [ValueError("Invalid settings"), MemoryError()])
def test_simulation_failure_clears_stale_chart_and_persists(failure: Exception) -> None:
    """Failed reruns remove previous outcomes without losing the portfolio."""
    app = submit(AppTest.from_file(APP_PATH).run())
    click_button(app, "Run hypothetical simulations")
    with patch("risklens.analytics.simulate_portfolio", side_effect=failure):
        click_button(app, "Run hypothetical simulations")
    assert not app.exception and app.error
    assert "simulation_chart" not in [chart.key for chart in app.get("plotly_chart")]
    app.checkbox[0].uncheck().run()
    assert app.error and not app.exception
    assert app.metric[0].label == "Annualized return"


def test_custom_stress_metrics_chart_and_invalid_dates(prices: pd.DataFrame, download: MagicMock) -> None:
    """Custom replay uses API metrics, dated wealth and inclusive download dates."""
    app = submit(AppTest.from_file(APP_PATH).run())
    next(widget for widget in app.selectbox if widget.label == "Historical scenario").select("Custom date range").run()
    expected = stress_test(prices, [0.5, 0.5], custom_scenario(prices.index[0], prices.index[-1]))
    with patch("risklens.analytics.stress_test", wraps=stress_test) as engine:
        click_button(app, "Run historical stress test")
        engine.assert_called_once()
    assert not app.exception and not app.error
    assert download.call_args.kwargs["end"] == date(2026, 1, 9)
    cards = {card.label: card.value for card in app.metric}
    assert cards["Scenario return"] == f"{expected.cumulative_return:.2%}"
    assert cards["Scenario maximum drawdown"] == f"{expected.max_drawdown:.2%}"
    assert cards["Scenario annualized volatility"] == f"{expected.annualized_volatility:.2%}"
    trace = chart_spec(app, "stress_chart")["data"][0]
    wealth = cumulative_wealth(portfolio_returns(to_returns(prices), [0.5, 0.5])).reindex(prices.index, fill_value=1.0)
    np.testing.assert_allclose(chart_values(trace["y"]), wealth)
    assert pd.to_datetime(trace["x"]).tolist() == prices.index.tolist()
    assert any("not the portfolio's actual historical holdings" in caption.value for caption in app.caption)
    calls = download.call_count
    next(widget for widget in app.date_input if widget.label == "Scenario start date").set_value(date(2026, 1, 9)).run()
    assert not app.exception and any("before" in note.value for note in app.warning)
    assert download.call_count == calls
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]


@pytest.mark.parametrize("scenario", HISTORICAL_SCENARIOS, ids=lambda scenario: scenario.name)
def test_historical_scenarios_use_their_own_download_window(scenario, prices: pd.DataFrame, download: MagicMock) -> None:
    """Older scenarios fetch their own history rather than using dashboard dates."""
    app = submit(AppTest.from_file(APP_PATH).run())
    history = prices.copy()
    history.index = pd.DatetimeIndex([scenario.start, scenario.start + pd.offsets.BDay(1), scenario.end - pd.offsets.BDay(1), scenario.end])
    download.return_value = pd.concat({"Close": history}, axis=1)
    next(widget for widget in app.selectbox if widget.label == "Historical scenario").select(scenario.name).run()
    click_button(app, "Run historical stress test")
    assert not app.exception and not app.error and not any("Scenario unavailable" in note.value for note in app.warning)
    assert download.call_args.kwargs["start"] == scenario.start.date()
    assert chart_spec(app, "stress_chart")["data"]
    next(widget for widget in app.selectbox if widget.label == "Historical scenario").select("Custom date range").run()
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]


@pytest.mark.parametrize("failure", ["insufficient", "short", "network"])
def test_stress_unavailable_preserves_dashboard(failure: str, prices: pd.DataFrame, download: MagicMock) -> None:
    """Incomplete history and failed downloads never present scenario metrics."""
    app = submit(AppTest.from_file(APP_PATH).run())
    if failure == "short":
        next(widget for widget in app.selectbox if widget.label == "Historical scenario").select("Custom date range").run()
        download.return_value = pd.concat({"Close": prices.iloc[:2]}, axis=1)
    elif failure == "network":
        download.side_effect = RuntimeError("Offline")
    click_button(app, "Run historical stress test")
    assert not app.exception and any("Scenario unavailable" in note.value for note in app.warning)
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]
    assert app.metric[0].label == "Annualized return"
    app.checkbox[0].uncheck().run()
    assert any("Scenario unavailable" in note.value for note in app.warning)


def test_new_analysis_resets_both_scenario_tools() -> None:
    """A new request cannot retain simulations or stress results from old inputs."""
    app = submit(AppTest.from_file(APP_PATH).run())
    click_button(app, "Run hypothetical simulations")
    next(widget for widget in app.selectbox if widget.label == "Historical scenario").select("Custom date range").run()
    click_button(app, "Run historical stress test")
    assert "simulation" in app.session_state["analysis"] and "stress" in app.session_state["analysis"]
    click_button(app, "Analyze portfolio")
    assert not app.exception
    assert "simulation" not in app.session_state["analysis"] and "stress" not in app.session_state["analysis"]
