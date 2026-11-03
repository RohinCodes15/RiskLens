"""Dashboard factor exposure and sector/country breakdown (downloads mocked)."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from risklens.analytics import FACTOR_COLUMNS, analyze_portfolio, factor_exposure
from risklens.data import DataFetchError

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(4)
    index = pd.bdate_range("2025-01-02", periods=200, name="Date")
    returns = rng.normal(0.0004, [0.012, 0.009, 0.008], (200, 3))
    return pd.DataFrame(
        np.cumprod(1 + returns, axis=0) * [150.0, 300.0, 450.0],
        index=index,
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture
def factors(prices: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(8)
    data = rng.normal(0, 0.01, (len(prices), len(FACTOR_COLUMNS)))
    return pd.DataFrame(data, index=prices.index, columns=FACTOR_COLUMNS).assign(RF=0.0001)


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def widget(widgets: object, label: str) -> object:
    return next(item for item in widgets if item.label == label)


def load_sources(factors: object) -> AppTest:
    labels = pd.DataFrame(
        {"sector": ["Technology", "Technology"], "country": ["United States", "Ireland"]},
        index=["AAPL", "MSFT"],
    )
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2025, 1, 1))
    app = widget(app.button, "Analyze portfolio").click().run()
    with (
        patch("risklens.data.fetch_factors", side_effect=[factors]),
        patch("risklens.data.fetch_classifications", return_value=labels),
    ):
        return widget(app.button, "Load factor and sector data").click().run()


def test_shows_factor_cards_and_sector_country_tables(
    prices: pd.DataFrame, factors: pd.DataFrame
) -> None:
    app = load_sources(factors)
    assert not app.exception and not app.error
    daily = analyze_portfolio(prices[["AAPL", "MSFT"]], [0.5, 0.5]).daily_returns
    expected = factor_exposure(daily, factors)
    cards = {card.label: card.value for card in app.metric}
    assert cards["Market beta"] == f"{expected.betas['Mkt-RF']:.2f}"
    assert cards["R²"] == f"{expected.r_squared:.2f}"
    tables = {frame.value.index.name: frame.value for frame in app.dataframe}
    assert tables["Sector"].loc["Technology", "Weight"] == pytest.approx(1.0)
    assert tables["Sector"].loc["Technology", "Share of risk"] == pytest.approx(1.0)
    assert set(tables["Country"].index) == {"United States", "Ireland"}
    assert tables["Country"]["Share of risk"].sum() == pytest.approx(1.0)


def test_factor_download_failure_shows_warning(factors: pd.DataFrame) -> None:
    app = load_sources(DataFetchError("offline"))
    assert not app.exception
    assert any("offline" in warning.value for warning in app.warning)
