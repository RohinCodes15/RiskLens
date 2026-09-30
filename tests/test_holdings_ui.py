"""Holdings entered as shares or dollar values drive the dashboard's weights."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import analyze_portfolio

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def prices() -> pd.DataFrame:
    """Three months of prices for three stocks plus SPY, served by ticker."""
    rng = np.random.default_rng(11)
    index = pd.bdate_range("2026-01-05", periods=60, name="Date")
    growth = np.cumprod(1 + rng.normal(0.0005, 0.012, (60, 4)), axis=0)
    return pd.DataFrame(
        growth * [200.0, 400.0, 90.0, 500.0],
        index=index,
        columns=["AAPL", "MSFT", "TLT", "SPY"],
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    """Serve the requested tickers' prices without touching Yahoo Finance."""

    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def enter_holdings(kind: str, amounts: dict[str, float]) -> AppTest:
    """Pick a holdings input, fill one amount per ticker, and set the dates."""
    app = AppTest.from_file(APP_PATH).run()
    widget(app.radio, "Enter holdings as").set_value(kind).run()
    suffix = {"Shares": "shares", "Dollar values": "value ($)"}[kind]
    for ticker, amount in amounts.items():
        widget(app.number_input, f"{ticker} {suffix}").set_value(amount)
    app.date_input[0].set_value(date(2026, 1, 1))
    app.date_input[1].set_value(date(2026, 3, 31))
    return app


def analyze(app: AppTest) -> AppTest:
    return widget(app.button, "Analyze portfolio").click().run()


def captions(app: AppTest) -> str:
    return " ".join(caption.value for caption in app.caption)


def test_shares_are_valued_at_the_last_close(prices: pd.DataFrame) -> None:
    last = prices.iloc[-1]
    values = np.array([10 * last["AAPL"], 4 * last["MSFT"]])
    expected = values / values.sum()
    with patch("risklens.analytics.analyze_portfolio", wraps=analyze_portfolio) as engine:
        app = analyze(enter_holdings("Shares", {"AAPL": 10.0, "MSFT": 4.0}))
    assert not app.exception and not app.error
    np.testing.assert_allclose(engine.call_args.args[1], expected)
    assert (
        f"Portfolio value: ${values.sum():,.2f}, with shares valued at "
        f"{prices.index[-1]:%b %d, %Y} closes." in captions(app)
    )
    assert f"AAPL {expected[0]:.2%} · MSFT {expected[1]:.2%}" in captions(app)


def test_dollar_values_become_weights() -> None:
    with patch("risklens.analytics.analyze_portfolio", wraps=analyze_portfolio) as engine:
        app = analyze(enter_holdings("Dollar values", {"AAPL": 3000.0, "MSFT": 1000.0}))
    assert not app.exception and not app.error
    np.testing.assert_allclose(engine.call_args.args[1], [0.75, 0.25])
    assert "Portfolio value: $4,000.00." in captions(app)


def test_holdings_default_to_zero_and_must_not_all_be_zero() -> None:
    app = enter_holdings("Shares", {})
    assert [widget(app.number_input, f"{t} shares").value for t in ("AAPL", "MSFT")] == [0.0, 0.0]
    app = analyze(app)
    assert not app.exception
    assert [error.value for error in app.error] == [
        "Unable to analyze this portfolio. Enter at least one holding above zero."
    ]
    assert not app.metric


def test_percent_weights_stay_the_default_without_a_portfolio_value() -> None:
    app = AppTest.from_file(APP_PATH).run()
    assert widget(app.radio, "Enter holdings as").value == "Percent weights"
    app.date_input[0].set_value(date(2026, 1, 1))
    app = analyze(app)
    assert not app.exception and not app.error
    assert "Portfolio value" not in captions(app)
