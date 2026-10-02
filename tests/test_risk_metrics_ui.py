"""Dashboard Sortino/Calmar cards, VaR models and backtest, and SPY ratios."""

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
    """300 trading days of two fat-tailed stocks and SPY, served by ticker."""
    rng = np.random.default_rng(21)
    index = pd.bdate_range("2025-01-02", periods=300, name="Date")
    returns = rng.standard_t(4, (300, 3)) * [0.012, 0.009, 0.008] + [0.0006, 0.0003, 0.0004]
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * [150.0, 300.0, 450.0],
        index=index,
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def analyze(rebalance: str | None = None, cost_bps: float | None = None) -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    if rebalance is not None:
        widget(app.selectbox, "Rebalancing").select(rebalance)
    if cost_bps is not None:
        widget(app.number_input, "Trading cost (bps)").set_value(cost_bps)
    app.date_input[0].set_value(date(2025, 1, 1))
    return widget(app.button, "Analyze portfolio").click().run()


def cards(app: AppTest) -> dict[str, str]:
    return {card.label: card.value for card in app.metric}


def test_ratio_cards_follow_rebalancing_and_costs(prices: pd.DataFrame) -> None:
    app = analyze("Monthly", 25.0)
    assert not app.exception and not app.error
    expected = analyze_portfolio(
        prices[["AAPL", "MSFT"]], [0.5, 0.5], rebalance="monthly", cost_bps=25.0
    )
    assert cards(app)["Sortino ratio"] == f"{expected.sortino_ratio:.2f}"
    assert cards(app)["Calmar ratio"] == f"{expected.calmar_ratio:.2f}"
    labels = [card.label for card in app.metric]
    assert labels.index("Sortino ratio") == labels.index("Maximum drawdown") + 1
