"""Dashboard volatility forecast: historical, EWMA and GARCH cards plus the dated chart."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import chart_spec, chart_values

from risklens.analytics import (
    analyze_portfolio,
    ewma_volatility,
    fit_garch,
    garch_forecast,
    horizon_volatility,
)

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


def make_prices(periods: int) -> pd.DataFrame:
    rng = np.random.default_rng(41)
    index = pd.bdate_range("2024-01-02", periods=periods, name="Date")
    returns = rng.normal(0.0004, [0.013, 0.010, 0.009], (periods, 3))
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * [150.0, 300.0, 450.0],
        index=index,
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture
def prices() -> pd.DataFrame:
    return make_prices(400)


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def analyzed() -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2024, 1, 1))
    return (
        next(button for button in app.button if button.label == "Analyze portfolio").click().run()
    )


def cards(app: AppTest) -> dict[str, str]:
    return {card.label: card.value for card in app.metric}


def test_cards_and_chart_match_the_api(prices: pd.DataFrame) -> None:
    app = analyzed()
    assert not app.exception and not app.error
    daily = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5]).daily_returns
    ewma, garch = ewma_volatility(daily), fit_garch(daily)
    shown = cards(app)
    assert shown["Historical volatility"] == f"{daily.std() * np.sqrt(252):.2%}"
    assert shown["EWMA volatility (next day)"] == f"{ewma.iloc[-1]:.2%}"
    expected = horizon_volatility(garch_forecast(garch, 21))
    assert shown["GARCH (next 21 days)"] == f"{expected:.2%}"
    assert shown["GARCH long-run volatility"] == f"{garch.long_run_volatility:.2%}"
    figure = chart_spec(app, "volatility_chart")
    assert [trace["name"] for trace in figure["data"]] == ["EWMA (λ = 0.94)", "GARCH(1,1)"]
    np.testing.assert_allclose(chart_values(figure["data"][0]["y"]), ewma)
    np.testing.assert_allclose(chart_values(figure["data"][1]["y"]), garch.conditional_volatility)
    assert any("α + β" in caption.value for caption in app.caption)


def test_horizon_changes_only_the_garch_card(prices: pd.DataFrame) -> None:
    app = analyzed()
    before = cards(app)
    label = "Volatility forecast horizon (trading days)"
    next(item for item in app.number_input if item.label == label).set_value(126).run()
    after = cards(app)
    daily = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5]).daily_returns
    expected = horizon_volatility(garch_forecast(fit_garch(daily), 126))
    assert after["GARCH (next 126 days)"] == f"{expected:.2%}"
    assert after["EWMA volatility (next day)"] == before["EWMA volatility (next day)"]


def test_short_history_keeps_ewma_and_explains_garch(prices: pd.DataFrame) -> None:
    short = prices.iloc[:120]
    with patch(
        "yfinance.download",
        side_effect=lambda tickers, **_: pd.concat({"Close": short[list(tickers)]}, axis=1),
    ):
        app = analyzed()
    assert not app.exception
    assert "EWMA volatility (next day)" in cards(app)
    assert "GARCH long-run volatility" not in cards(app)
    assert any("GARCH(1,1) forecast is unavailable" in info.value for info in app.info)
    figure = chart_spec(app, "volatility_chart")
    assert [trace["name"] for trace in figure["data"]] == ["EWMA (λ = 0.94)"]
