"""End-to-end stress replays retain each ticker's own adjusted-price dates."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_risk_ui import analyzed_app, select
from test_smoke import chart_spec, chart_values, click_button

from risklens.analytics import (
    HISTORICAL_SCENARIOS,
    cumulative_wealth,
    portfolio_returns,
    stress_test,
)
from risklens.data import to_returns


@pytest.fixture
def app() -> AppTest:
    """Analyze a valid current portfolio without accessing Yahoo Finance."""
    current = pd.DataFrame(
        {"AAPL": [100.0, 90.0, 108.0, 105.0], "MSFT": [200.0, 210.0, 189.0, 205.0]},
        index=pd.bdate_range("2026-01-05", periods=4),
    )
    result = analyzed_app(current, tickers="AAPL, MSFT")
    select(result, "Historical scenario", HISTORICAL_SCENARIOS[1].name)
    return result


@pytest.fixture
def history() -> pd.DataFrame:
    """Independent observations spanning the COVID window, with an early loss."""
    scenario = HISTORICAL_SCENARIOS[1]
    dates = [scenario.start + pd.offsets.BDay(n) for n in [0, 1, 6, 7, 8]]
    return pd.DataFrame(
        {"AAPL": [100.0, 90.0, 95.0, 80.0, 85.0, 75.0],
         "MSFT": [200.0, 190.0, 180.0, 195.0, 170.0, 160.0]},
        index=pd.DatetimeIndex([*dates, scenario.end]),
    )


def test_late_listing_names_only_the_stock_with_insufficient_history(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """An older stock must not inherit the newer stock's first observed date."""
    history.loc[history.index[:2], "MSFT"] = np.nan
    raw = pd.concat({"Close": history}, axis=1)
    with patch("yfinance.download", return_value=raw), patch(
        "risklens.analytics.stress_test", wraps=stress_test,
    ) as engine:
        click_button(app, "Run historical stress test")
    assert not app.exception and not app.error
    pd.testing.assert_frame_equal(engine.call_args.args[0], history)
    message = next(note.value for note in app.warning if "Scenario unavailable" in note.value)
    assert f"MSFT history starts {history.index[2].date()}" in message
    assert "Insufficient history" in message and "AAPL history starts" not in message
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]
    assert not any(card.label == "Scenario return" for card in app.metric)
    assert app.metric[0].label == "Annualized return"
