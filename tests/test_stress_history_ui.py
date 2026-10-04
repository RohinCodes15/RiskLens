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
