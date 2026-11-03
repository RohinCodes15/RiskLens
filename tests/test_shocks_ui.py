"""Dashboard custom shocks tab: proxy download, portfolio move, and holding table."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import shock_impact
from risklens.data import to_returns

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
TICKERS = ["AAPL", "MSFT", "SPY", "XLK", "TLT"]


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(31)
    index = pd.bdate_range("2025-01-02", periods=150, name="Date")
    returns = rng.normal(0.0004, [0.014, 0.011, 0.009, 0.012, 0.006], (150, 5))
    return pd.DataFrame(np.cumprod(1 + returns, axis=0) * 100.0, index=index, columns=TICKERS)


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def analyzed() -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2025, 1, 1))
    return widget(app.button, "Analyze portfolio").click().run()


def shocked(moves: dict[str, float]) -> AppTest:
    app = analyzed()
    for label, move in moves.items():
        widget(app.number_input, label).set_value(move)
    app.run()  # a changed input reruns the page, which enables the button
    return widget(app.button, "Apply shocks").click().run()


def test_apply_waits_for_a_non_zero_move() -> None:
    app = analyzed()
    assert not app.exception
    assert widget(app.button, "Apply shocks").disabled
    assert any("non-zero move" in info.value for info in app.info)


def test_shock_matches_the_api_and_downloads_only_the_proxy(
    prices: pd.DataFrame, download: MagicMock
) -> None:
    app = shocked({"Technology (XLK) move (%)": -20.0, "Long-term bonds (TLT) move (%)": 5.0})
    assert not app.exception and not app.warning
    assert download.call_args.args[0] == ["XLK", "TLT"]
    proxies = to_returns(prices[["XLK", "TLT"]]).rename(
        columns={"XLK": "Technology", "TLT": "Long-term bonds"}
    )
    expected = shock_impact(
        to_returns(prices[["AAPL", "MSFT"]]),
        proxies,
        [0.5, 0.5],
        {"Technology": -0.2, "Long-term bonds": 0.05},
    )
    cards = {card.label: card.value for card in app.metric}
    assert cards["Estimated portfolio move"] == f"{expected.portfolio_impact:.2%}"
    table = next(frame.value for frame in app.dataframe if "Estimated move" in frame.value)
    assert list(table.index) == ["AAPL", "MSFT"]
    assert table["Estimated move"].to_numpy() == pytest.approx(
        expected.holdings["impact"].to_numpy()
    )
    assert table["Beta to Technology"].to_numpy() == pytest.approx(
        expected.betas["Technology"].to_numpy()
    )
    captions = " ".join(caption.value for caption in app.caption)
    assert "Shocks: Technology -20.0%, Long-term bonds +5.0%" in captions


def test_download_failure_shows_a_warning(download: MagicMock) -> None:
    app = analyzed()
    widget(app.number_input, "Gold (GLD) move (%)").set_value(10.0).run()
    download.side_effect = ConnectionError("offline")
    app = widget(app.button, "Apply shocks").click().run()
    assert not app.exception
    assert any("offline" in warning.value for warning in app.warning)
    assert "Estimated portfolio move" not in {card.label for card in app.metric}


def test_changing_a_move_hides_the_old_estimate() -> None:
    app = shocked({"Market (SPY) move (%)": -10.0})
    assert "Estimated portfolio move" in {card.label for card in app.metric}
    widget(app.number_input, "Market (SPY) move (%)").set_value(-15.0).run()
    assert "Estimated portfolio move" not in {card.label for card in app.metric}
