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


@pytest.mark.parametrize("omitted_column", [False, True])
def test_stock_without_crisis_prices_has_an_accurate_unavailable_message(
    app: AppTest, history: pd.DataFrame, omitted_column: bool,
) -> None:
    """A stock listed after the crisis has no prices, not a shared start date."""
    history["MSFT"] = np.nan
    raw = pd.concat({"Close": history.drop(columns="MSFT") if omitted_column else history}, axis=1)
    with patch("yfinance.download", return_value=raw):
        click_button(app, "Run historical stress test")
    assert not app.exception and not app.error
    assert any("MSFT has no price data" in note.value for note in app.warning)
    assert not any("AAPL history starts" in note.value for note in app.warning)
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]
    assert app.metric[0].label == "Annualized return"


@pytest.mark.parametrize("missing_day", [False, True])
def test_valid_stress_history_matches_backend_and_omits_missing_dates(
    app: AppTest, history: pd.DataFrame, missing_day: bool,
) -> None:
    """Valid replays use only complete dates, never fill a missing stock price."""
    if missing_day:
        history.loc[history.index[2], "MSFT"] = np.nan
    scenario = HISTORICAL_SCENARIOS[1]
    expected = stress_test(history, [0.5, 0.5], scenario)
    assert expected.available
    with patch("yfinance.download", return_value=pd.concat({"Close": history}, axis=1)) as download:
        click_button(app, "Run historical stress test")
    assert not app.exception and not app.error
    assert not any("Scenario unavailable" in note.value for note in app.warning)
    assert download.call_args.args[0] == ["AAPL", "MSFT"]
    assert download.call_args.kwargs["auto_adjust"] is True
    assert download.call_args.kwargs["start"] == scenario.start.date()
    assert download.call_args.kwargs["end"] == (scenario.end + pd.Timedelta(days=1)).date()
    cards = {card.label: card.value for card in app.metric}
    assert cards["Scenario return"] == f"{expected.cumulative_return:.2%}"
    assert cards["Scenario maximum drawdown"] == f"{expected.max_drawdown:.2%}"
    assert cards["Scenario annualized volatility"] == f"{expected.annualized_volatility:.2%}"
    complete = history.dropna()
    wealth = cumulative_wealth(portfolio_returns(to_returns(complete), [0.5, 0.5]))
    trace = chart_spec(app, "stress_chart")["data"][0]
    assert pd.to_datetime(trace["x"]).tolist() == complete.index.tolist()
    np.testing.assert_allclose(chart_values(trace["y"]), wealth.reindex(complete.index, fill_value=1.0))


def replay(app: AppTest, history: pd.DataFrame) -> AppTest:
    """Run the selected scenario against mocked adjusted Close prices."""
    with patch("yfinance.download", return_value=pd.concat({"Close": history}, axis=1)):
        return click_button(app, "Run historical stress test")


def unavailable(app: AppTest) -> str:
    """Return the one scenario-unavailable warning shown by the stress section."""
    return next(note.value for note in app.warning if "Scenario unavailable" in note.value)


def test_delisted_stock_names_its_last_price_before_the_crisis_end(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """A stock whose prices stop early is blamed with its own last date."""
    history.loc[history.index[-2:], "AAPL"] = np.nan
    replay(app, history)
    assert not app.exception and not app.error
    message = unavailable(app)
    assert f"AAPL history ends {history.index[3].date()}" in message
    assert "MSFT history" not in message
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]


def test_every_late_listed_stock_is_named_with_its_own_start(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """Two late listings report two different first dates, never a shared one."""
    history.loc[history.index[:2], "AAPL"] = np.nan
    history.loc[history.index[:3], "MSFT"] = np.nan
    replay(app, history)
    assert not app.exception and not app.error
    message = unavailable(app)
    assert f"AAPL history starts {history.index[2].date()}" in message
    assert f"MSFT history starts {history.index[3].date()}" in message


def test_too_few_common_dates_is_unavailable_without_filling_prices(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """Covering stocks with only two shared dates must not be forward-filled."""
    history.loc[history.index[1:5], "MSFT"] = np.nan
    replay(app, history)
    assert not app.exception and not app.error
    assert "Need 3 common price dates in the window; got 2." in unavailable(app)
    assert not any(card.label == "Scenario return" for card in app.metric)
