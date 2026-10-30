"""Network-free dashboard checks using mocked downloads and the analytics API."""

import base64
from collections.abc import Iterator
from datetime import date
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import (
    analyze_portfolio, compare_to_benchmark, drawdown_series, effective_holdings, herfindahl_index,
)

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
        assert [card.label for card in app.metric] == [
            "Annualized return", "Annualized volatility", "Sharpe ratio", "Maximum drawdown",
            "HHI concentration", "Effective number of holdings",
        ]
        assert [card.value for card in app.metric] == [
            f"{expected.annualized_return:.2%}", f"{expected.annualized_volatility:.2%}",
            f"{expected.sharpe_ratio:.2f}", f"{expected.max_drawdown:.2%}",
            f"{herfindahl_index([0.6, 0.4]):.3f}", f"{effective_holdings([0.6, 0.4]):.2f}",
        ]
        pd.testing.assert_frame_equal(engine.call_args.args[0], prices)
        np.testing.assert_allclose(engine.call_args.args[1], [0.6, 0.4])
        assert download.call_args.kwargs["end"] == date(2026, 1, 11)
        assert download.call_args.kwargs["auto_adjust"] is True
        # TODO(human): Replace the next line with the 12 chart assertions (eight spaces).
        pytest.skip("Complete the drawdown assertions before running this test.")
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
    assert [card.value for card in app.metric] == ["0.00%", "0.00%", "N/A", "0.00%", "0.500", "2.00"]
    assert len(app.get("plotly_chart")) == 3
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
    assert [card.value for card in app.metric][4:] == ["1.000", "1.00"]
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
    assert not app.exception and not app.error and not app.warning
    assert "benchmark_chart" in [chart.key for chart in app.get("plotly_chart")]
    assert [(card.label, card.value) for card in app.metric][-2:] == [
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
