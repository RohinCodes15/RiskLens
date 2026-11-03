"""Dashboard what-if trade tab: before/after tables, new-ticker downloads, and errors."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import compare_portfolios, trade_weights

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
TICKERS = ["AAPL", "MSFT", "TLT", "SPY"]


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(21)
    index = pd.bdate_range("2025-01-02", periods=150, name="Date")
    returns = rng.normal(0.0004, [0.014, 0.011, 0.006, 0.009], (150, 4))
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * [150.0, 300.0, 90.0, 450.0],
        index=index,
        columns=TICKERS,
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        if "FAIL" in tickers:
            raise ConnectionError("offline")
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def analyzed(cost_bps: float = 0.0) -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2025, 1, 1))
    widget(app.number_input, "Trading cost (bps)").set_value(cost_bps)
    return widget(app.button, "Analyze portfolio").click().run()


def simulate(app: AppTest, sell: str, buy: str, amount: float) -> AppTest:
    widget(app.selectbox, "Sell").select(sell)
    widget(app.text_input, "Buy").set_value(buy)
    widget(app.number_input, "Amount (% of portfolio)").set_value(amount)
    return widget(app.button, "Simulate trade").click().run()


def tables(app: AppTest) -> dict[str, pd.DataFrame]:
    return {frame.value.index.name: frame.value for frame in app.dataframe}


def expected_metrics(prices: pd.DataFrame, sell: str, buy: str, amount: float) -> pd.DataFrame:
    before = pd.Series([0.5, 0.5], index=["AAPL", "MSFT"])
    after = trade_weights(before, sell, buy, amount)
    return compare_portfolios(prices[list(after.index)], before, after)


def test_waits_for_the_button() -> None:
    app = analyzed()
    assert not app.exception
    assert any("select Simulate trade" in info.value for info in app.info)
    assert "Metric" not in tables(app)


def test_trade_between_held_tickers_needs_no_download(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    app = analyzed()
    calls = download.call_count
    app = simulate(app, "AAPL", "msft", 10.0)
    assert not app.exception and not app.warning
    assert download.call_count == calls
    shown = tables(app)
    assert shown["Ticker"].to_dict() == {
        "Before": pytest.approx({"AAPL": 0.5, "MSFT": 0.5}),
        "After": pytest.approx({"AAPL": 0.4, "MSFT": 0.6}),
    }
    expected = expected_metrics(prices, "AAPL", "MSFT", 0.1)
    metrics = shown["Metric"]
    assert metrics.loc["Annualized volatility", "Before"] == (
        f"{expected.loc['annualized_volatility', 'before']:.2%}"
    )
    assert metrics.loc["Annualized volatility", "After"] == (
        f"{expected.loc['annualized_volatility', 'after']:.2%}"
    )
    assert metrics.loc["Sharpe ratio", "Change"] == f"{expected.loc['sharpe_ratio', 'change']:+.2f}"
    assert list(metrics.columns) == ["Before", "After", "Change"]


def test_buying_a_new_ticker_downloads_it_for_the_same_dates(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    app = simulate(analyzed(), "MSFT", "TLT", 25.0)
    assert not app.exception and not app.warning
    assert download.call_args.args[0] == ["AAPL", "MSFT", "TLT"]
    assert download.call_args.kwargs["start"] == prices.index[0].date()
    assert tables(app)["Ticker"].loc["TLT", "After"] == pytest.approx(0.25)
    expected = expected_metrics(prices, "MSFT", "TLT", 0.25)
    assert tables(app)["Metric"].loc["One-day VaR (95%)", "After"] == (
        f"{expected.loc['var', 'after']:.2%}"
    )


def test_caption_reports_the_one_time_trade_cost() -> None:
    app = simulate(analyzed(cost_bps=10.0), "AAPL", "TLT", 10.0)
    captions = " ".join(caption.value for caption in app.caption)
    assert "Moves 10.00% of the portfolio from AAPL to TLT" in captions
    assert "0.020% of the portfolio" in captions


@pytest.mark.parametrize(
    ("sell", "buy", "amount", "message"),
    [
        ("AAPL", "TLT", 60.0, "it is only 50.00%"),
        ("AAPL", "AAPL", 10.0, "different ticker"),
        ("AAPL", "TLT GLD", 10.0, "Enter one ticker to buy"),
        ("AAPL", "", 10.0, "Enter at least one ticker"),
        ("AAPL", "FAIL", 10.0, "offline"),
    ],
)
def test_bad_trades_show_a_warning(sell: str, buy: str, amount: float, message: str) -> None:
    app = simulate(analyzed(), sell, buy, amount)
    assert not app.exception
    assert any(message in warning.value for warning in app.warning)
    assert "Metric" not in tables(app)


def test_changing_the_trade_hides_the_old_result() -> None:
    app = simulate(analyzed(), "AAPL", "MSFT", 10.0)
    widget(app.number_input, "Amount (% of portfolio)").set_value(20.0).run()
    assert "Metric" not in tables(app)
    assert any("select Simulate trade" in info.value for info in app.info)
