"""Dashboard risk attribution and sector table with rebalancing and trading costs."""

from collections.abc import Iterator
from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_smoke import APP_PATH, chart_spec, chart_values, click_button

from risklens.analytics import COST_LABEL, group_breakdown, rebalanced_risk_contributions
from risklens.data import to_returns


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(61)
    daily = rng.normal(0.0004, [0.015, 0.009, 0.008], (180, 3))
    return pd.DataFrame(
        100 * np.cumprod(1 + daily, axis=0),
        index=pd.bdate_range("2025-01-02", periods=180, name="Date"),
        columns=["AAPL", "MSFT", "SPY"],
    )


@pytest.fixture(autouse=True)
def download(prices: pd.DataFrame) -> Iterator[MagicMock]:
    def fake_download(tickers: list[str], **_: object) -> pd.DataFrame:
        return pd.concat({"Close": prices[list(tickers)]}, axis=1)

    with patch("yfinance.download", side_effect=fake_download) as mock:
        yield mock


def analyzed(rebalance: str, cost_bps: float) -> AppTest:
    app = AppTest.from_file(APP_PATH).run()
    app.date_input[0].set_value(date(2025, 1, 1))
    next(box for box in app.selectbox if box.label == "Rebalancing").select(rebalance)
    next(n for n in app.number_input if n.label == "Trading cost (bps)").set_value(cost_bps)
    return click_button(app, "Analyze portfolio")


def test_chart_follows_rebalancing_and_shows_trading_costs(prices: pd.DataFrame) -> None:
    app = analyzed("Monthly", 25.0)
    assert not app.exception and not app.error
    expected = rebalanced_risk_contributions(
        to_returns(prices[["AAPL", "MSFT"]]), [0.5, 0.5], "monthly", 25.0
    )
    allocation, risk = chart_spec(app, "risk_attribution_chart")["data"]
    assert list(risk["x"]) == ["AAPL", "MSFT", COST_LABEL]
    np.testing.assert_allclose(chart_values(risk["y"]), expected.to_numpy())
    np.testing.assert_allclose(chart_values(allocation["y"]), [0.5, 0.5, 0.0])
    captions = " ".join(caption.value for caption in app.caption)
    assert "reset to target each month" in captions
    assert f"{COST_LABEL} is the drag from rebalancing trades" in captions


def test_without_costs_there_is_no_cost_bar() -> None:
    app = analyzed("Never (buy and hold)", 0.0)
    _, risk = chart_spec(app, "risk_attribution_chart")["data"]
    assert list(risk["x"]) == ["AAPL", "MSFT"]
    assert "drag from rebalancing" not in " ".join(c.value for c in app.caption)


def test_sector_table_uses_the_same_rebalanced_shares(prices: pd.DataFrame) -> None:
    app = analyzed("Quarterly", 10.0)
    labels = pd.DataFrame(
        {"sector": ["Technology", "Technology"], "country": ["United States", "Ireland"]},
        index=["AAPL", "MSFT"],
    )
    factors = pd.DataFrame(
        np.random.default_rng(1).normal(0, 0.01, (len(prices), 4)),
        index=prices.index,
        columns=["Mkt-RF", "SMB", "HML", "Mom"],
    ).assign(RF=0.0001)
    with (
        patch("risklens.data.fetch_factors", return_value=factors),
        patch("risklens.data.fetch_classifications", return_value=labels),
    ):
        app = click_button(app, "Load factor and sector data")
    assert not app.exception
    shown = next(f.value for f in app.dataframe if f.value.index.name == "Sector")
    expected = group_breakdown(
        to_returns(prices[["AAPL", "MSFT"]]),
        [0.5, 0.5],
        labels["sector"].rename("Sector"),
        "quarterly",
        10.0,
    )
    assert shown.loc["Technology", "Share of risk"] == pytest.approx(
        expected.loc["Technology", "risk_share"]
    )
    assert shown.loc[COST_LABEL, "Weight"] == 0.0
