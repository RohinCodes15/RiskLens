"""Network-free Tail Risk dashboard regressions using the real analytics API."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import APP_PATH, chart_spec, chart_values, click_button

from risklens.analytics import analyze_portfolio, tail_risk_summary


@pytest.fixture
def app_data():
    """Provide actual synthetic adjusted prices; every download stays mocked."""
    daily = np.tile([-0.03, -0.01, 0.01, 0.02, 0.005], 30)
    prices = pd.DataFrame(
        {"AAPL": 100 * np.cumprod(1 + daily), "MSFT": 200 * np.cumprod(1 + daily / 2)},
        index=pd.bdate_range("2025-01-02", periods=len(daily)),
    )
    with patch("yfinance.download", return_value=pd.concat({"Close": prices}, axis=1)) as download:
        app = AppTest.from_file(APP_PATH).run()
        click_button(app, "Analyze portfolio")
        yield app, prices, download


def test_confidence_switch_uses_api_and_actual_histogram(app_data) -> None:
    """Cards and negative-loss cutoff match the API; switching never downloads."""
    app, prices, download = app_data
    daily = analyze_portfolio(prices, [0.5, 0.5]).daily_returns
    calls = download.call_count
    with patch("risklens.analytics.tail_risk_summary", wraps=tail_risk_summary) as engine:
        for confidence in [0.99, 0.95]:
            next(widget for widget in app.selectbox if widget.label == "Tail risk confidence").select(confidence).run()
            assert not app.exception and not app.error
            expected = tail_risk_summary(daily, (confidence,)).loc[confidence]
            cards = {card.label: card.value for card in app.metric}
            assert cards["One-day VaR"] == f"{expected['var']:.2%}"
            assert cards["One-day CVaR"] == f"{expected['cvar']:.2%}"
            pd.testing.assert_series_equal(engine.call_args.args[0], daily)
            assert engine.call_args.args[1] == (confidence,)
            figure = chart_spec(app, "tail_risk_histogram")
            assert figure["data"][0]["type"] == "histogram"
            np.testing.assert_allclose(chart_values(figure["data"][0]["x"]), daily)
            assert figure["layout"]["shapes"][0]["x0"] == pytest.approx(-expected["var"])
            assert not any("Small historical sample" in note.value for note in app.warning)
    assert download.call_count == calls


@pytest.mark.parametrize("confidence", [0.95, 0.99])
def test_small_sample_warning_and_zero_returns(app_data, confidence: float) -> None:
    """Short flat history stays honest: zero loss metrics and a sample warning."""
    app, _, _ = app_data
    analysis = app.session_state["analysis"]
    analysis["daily_returns"] = pd.Series([0.0, 0.0], index=pd.bdate_range("2025-01-02", periods=2))
    next(widget for widget in app.selectbox if widget.label == "Tail risk confidence").select(confidence).run()
    assert not app.exception
    cards = {card.label: float(card.value.rstrip("%")) for card in app.metric if card.label in {"One-day VaR", "One-day CVaR"}}
    assert cards == {"One-day VaR": 0.0, "One-day CVaR": 0.0}
    assert any("Small historical sample" in note.value for note in app.warning)


@pytest.mark.parametrize("bad", [pd.Series(dtype=float), pd.Series([np.nan, 0.01]), pd.Series([np.inf, 0.01])])
def test_invalid_tail_data_hides_risk_results(app_data, bad: pd.Series) -> None:
    """Backend rejection displays a warning without breaking other sections."""
    app, _, _ = app_data
    app.session_state["analysis"]["daily_returns"] = bad
    app.run()
    assert not app.exception
    assert any("Tail risk is unavailable" in note.value for note in app.warning)
    assert "tail_risk_histogram" not in [chart.key for chart in app.get("plotly_chart")]
    assert "One-day VaR" not in [card.label for card in app.metric]
    assert app.metric[0].label == "Annualized return"
