"""Holdings entered as shares or dollar values drive the dashboard's weights."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import analyze_portfolio, tail_risk_summary

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


def upload(app: AppTest, content: str, name: str = "holdings.csv") -> AppTest:
    return app.file_uploader[0].set_value((name, content.encode(), "text/csv")).run()


def test_csv_import_replaces_the_manual_inputs(prices: pd.DataFrame) -> None:
    app = upload(AppTest.from_file(APP_PATH).run(), 'ticker,value\nTLT,"$2,500.00"\nAAPL,7500\n')
    assert not app.exception and not app.error
    assert not app.text_input and not app.radio
    assert "Using 2 holdings from holdings.csv." in captions(app)
    app.date_input[0].set_value(date(2026, 1, 1))
    with patch("risklens.analytics.analyze_portfolio", wraps=analyze_portfolio) as engine:
        app = analyze(app)
    assert not app.exception and not app.error
    pd.testing.assert_frame_equal(engine.call_args.args[0], prices[["TLT", "AAPL"]])
    np.testing.assert_allclose(engine.call_args.args[1], [0.25, 0.75])
    assert "Portfolio value: $10,000.00." in captions(app)

    app = app.file_uploader[0].set_value(None).run()
    assert app.text_input[0].value == "AAPL, MSFT" and not app.metric


def test_csv_shares_are_valued_like_manual_shares(prices: pd.DataFrame) -> None:
    app = upload(AppTest.from_file(APP_PATH).run(), "Ticker,Shares\nMSFT,4\nAAPL,10\n")
    app.date_input[0].set_value(date(2026, 1, 1))
    with patch("risklens.analytics.analyze_portfolio", wraps=analyze_portfolio) as engine:
        app = analyze(app)
    values = np.array([4 * prices["MSFT"].iloc[-1], 10 * prices["AAPL"].iloc[-1]])
    np.testing.assert_allclose(engine.call_args.args[1], values / values.sum())


def test_bad_csv_lists_its_rows_and_blocks_analysis(download: MagicMock) -> None:
    app = upload(AppTest.from_file(APP_PATH).run(), "ticker,shares\nAAPL,abc\n,3\n", "bad.csv")
    assert not app.exception
    assert [error.value for error in app.error] == [
        "Could not import bad.csv. Line 2: Shares must be a number; got 'abc'. "
        "Line 3: Ticker is missing."
    ]
    assert widget(app.button, "Analyze portfolio").disabled
    assert not app.text_input
    download.assert_not_called()


def test_percent_weights_take_an_optional_portfolio_value() -> None:
    app = AppTest.from_file(APP_PATH).run()
    field = widget(app.number_input, "Portfolio value ($)")
    assert field.value is None
    field.set_value(100_000.0)
    app.date_input[0].set_value(date(2026, 1, 1))
    app = analyze(app)
    assert not app.exception and not app.error
    assert "Portfolio value: $100,000.00." in captions(app)


def test_share_and_dollar_holdings_need_no_separate_portfolio_value() -> None:
    app = enter_holdings("Shares", {"AAPL": 1.0})
    assert "Portfolio value ($)" not in [field.label for field in app.number_input]


def usd(fraction: float, value: float) -> str:
    """Expected card delta: a signed whole-dollar change."""
    amount = round(fraction * value)
    return f"{'-' if amount < 0 else '+' if amount > 0 else ''}${abs(amount):,}"


def test_portfolio_value_shows_drawdown_var_and_cvar_in_dollars(prices: pd.DataFrame) -> None:
    app = AppTest.from_file(APP_PATH).run()
    widget(app.number_input, "Portfolio value ($)").set_value(100_000.0)
    app.date_input[0].set_value(date(2026, 1, 1))
    app = analyze(app)
    assert not app.exception and not app.error
    result = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5])
    tail = tail_risk_summary(result.daily_returns, (0.95,)).loc[0.95]
    deltas = {card.label: card.delta for card in app.metric}
    assert deltas["Maximum drawdown"] == usd(result.max_drawdown, 100_000.0)
    assert deltas["Maximum drawdown"].startswith("-$")
    assert deltas["One-day VaR"] == usd(-tail["var"], 100_000.0)
    assert deltas["One-day CVaR"] == usd(-tail["cvar"], 100_000.0)
    assert "same changes on your $100,000.00 portfolio" in captions(app)


def test_cards_have_no_dollar_amounts_without_a_portfolio_value() -> None:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2026, 1, 1))
    app = analyze(app)
    assert not app.exception and app.metric
    assert not any(card.delta for card in app.metric)
