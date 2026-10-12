"""Network-free rolling-risk and risk-attribution dashboard checks using the real analytics API."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import APP_PATH, chart_spec, chart_values, click_button

from risklens.analytics import analyze_portfolio, risk_contributions, rolling_metrics
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
    [(21, "Volatility", "volatility"), (63, "Sharpe ratio", "sharpe"), (126, "Drawdown", "drawdown")],
)
def test_rolling_chart_matches_the_api(prices: pd.DataFrame, window: int, view: str, column: str) -> None:
    app = analyzed_app(prices)
    select(app, "Rolling window", window)
    select(app, "Rolling metric", view)
    assert not app.exception and not app.error
    weights = app.session_state["analysis"]["weights"]
    expected = rolling_metrics(analyze_portfolio(prices, weights).daily_returns, window)[column].dropna()
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
