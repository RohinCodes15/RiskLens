"""End-to-end stress replays retain each ticker's own adjusted-price dates."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_risk_ui import analyzed_app, select
from test_smoke import APP_PATH, chart_spec, chart_values, click_button

from risklens.analytics import (
    HISTORICAL_SCENARIOS,
    cumulative_wealth,
    custom_scenario,
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
        {
            "AAPL": [100.0, 90.0, 95.0, 80.0, 85.0, 75.0],
            "MSFT": [200.0, 190.0, 180.0, 195.0, 170.0, 160.0],
        },
        index=pd.DatetimeIndex([*dates, scenario.end]),
    )


def test_late_listing_names_only_the_stock_with_insufficient_history(
    app: AppTest,
    history: pd.DataFrame,
) -> None:
    """An older stock must not inherit the newer stock's first observed date."""
    history.loc[history.index[:2], "MSFT"] = np.nan
    raw = pd.concat({"Close": history}, axis=1)
    with (
        patch("yfinance.download", return_value=raw),
        patch(
            "risklens.analytics.stress_test",
            wraps=stress_test,
        ) as engine,
    ):
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
    app: AppTest,
    history: pd.DataFrame,
    omitted_column: bool,
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


@pytest.mark.parametrize(
    ("download", "reason"),
    [
        ({"side_effect": RuntimeError("timeout")}, "Price download failed: timeout"),
        ({"return_value": pd.DataFrame()}, "No price data returned for the requested range."),
    ],
)
def test_download_problems_show_a_warning_and_keep_the_analysis(
    app: AppTest, download: dict, reason: str,
) -> None:
    """Fetch errors stay inside the stress section instead of crashing the page."""
    with patch("yfinance.download", **download):
        click_button(app, "Run historical stress test")
    assert not app.exception and not app.error
    assert unavailable(app) == f"Scenario unavailable: {reason}"
    assert app.metric[0].label == "Annualized return"


def test_custom_window_after_a_late_listing_replays_successfully(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """Starting a custom range on the listing date makes the replay available."""
    history.loc[history.index[:2], "MSFT"] = np.nan
    start, end = history.index[2].date(), history.index[-1].date()
    select(app, "Historical scenario", "Custom date range")
    for label, value in [("Scenario start date", start), ("Scenario end date (inclusive)", end)]:
        next(widget for widget in app.date_input if widget.label == label).set_value(value).run()
    replay(app, history)
    assert not app.exception and not app.error
    assert not any("Scenario unavailable" in note.value for note in app.warning)
    expected = stress_test(history, [0.5, 0.5], custom_scenario(start, end))
    cards = {card.label: card.value for card in app.metric}
    assert cards["Scenario return"] == f"{expected.cumulative_return:.2%}"


def test_switching_scenarios_hides_the_previous_replay(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """A finished replay is never shown under a different scenario's name."""
    replay(app, history)
    assert any(card.label == "Scenario return" for card in app.metric)
    select(app, "Historical scenario", HISTORICAL_SCENARIOS[0].name)
    assert not app.exception and not app.error
    assert any("Run the selected scenario" in note.value for note in app.info)
    assert not any(card.label == "Scenario return" for card in app.metric)
    assert "stress_chart" not in [chart.key for chart in app.get("plotly_chart")]


def test_rerun_with_full_history_clears_the_unavailable_warning(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """A later successful replay replaces an earlier insufficient-history result."""
    late = history.copy()
    late["MSFT"] = np.nan
    replay(app, late)
    assert "MSFT has no price data" in unavailable(app)
    replay(app, history)
    assert not app.exception and not app.error
    assert not any("Scenario unavailable" in note.value for note in app.warning)
    assert "stress_chart" in [chart.key for chart in app.get("plotly_chart")]


def test_selected_scenario_waits_for_a_run_before_downloading(app: AppTest) -> None:
    """Choosing a crisis shows its requested window and prompt, not a result."""
    scenario = HISTORICAL_SCENARIOS[1]
    with patch("yfinance.download") as download:
        select(app, "Historical scenario", scenario.name)
    download.assert_not_called()
    assert not app.exception and not app.error
    window = f"Requested window: {scenario.start:%b %d, %Y} – {scenario.end:%b %d, %Y} (inclusive)."
    assert any(caption.value == window for caption in app.caption)
    assert any("Run the selected scenario" in note.value for note in app.info)
    assert not any(card.label == "Scenario return" for card in app.metric)


def test_replay_uses_the_analyzed_custom_weights(history: pd.DataFrame) -> None:
    """A 70/30 portfolio is replayed with 70/30 weights, not equal weights."""
    current = pd.DataFrame(
        {"AAPL": [100.0, 90.0, 108.0, 105.0], "MSFT": [200.0, 210.0, 189.0, 205.0]},
        index=pd.bdate_range("2026-01-05", periods=4),
    )
    with patch("yfinance.download", return_value=pd.concat({"Close": current}, axis=1)):
        app = AppTest.from_file(APP_PATH).run()
        app.text_input[0].set_value("AAPL, MSFT").run()
        for label, value in [("AAPL weight (%)", 70.0), ("MSFT weight (%)", 30.0)]:
            next(widget for widget in app.number_input if widget.label == label).set_value(value)
        click_button(app, "Analyze portfolio")
    select(app, "Historical scenario", HISTORICAL_SCENARIOS[1].name)
    replay(app, history)
    assert not app.exception and not app.error
    np.testing.assert_allclose(app.session_state["analysis"]["weights"], [0.7, 0.3])
    expected = stress_test(history, [0.7, 0.3], HISTORICAL_SCENARIOS[1])
    cards = {card.label: card.value for card in app.metric}
    assert cards["Scenario return"] == f"{expected.cumulative_return:.2%}"
    assert cards["Scenario maximum drawdown"] == f"{expected.max_drawdown:.2%}"


def test_actual_price_dates_caption_counts_only_complete_returns(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """The caption reports backend first/last dates and returns after a gap."""
    history.loc[history.index[2], "AAPL"] = np.nan
    expected = stress_test(history, [0.5, 0.5], HISTORICAL_SCENARIOS[1])
    replay(app, history)
    assert not app.exception and not app.error
    caption = (
        f"Actual price dates: {expected.first_date:%b %d, %Y} – {expected.last_date:%b %d, %Y}"
        f" · {expected.n_returns:,} return observations."
    )
    assert any(note.value == caption for note in app.caption)
    assert expected.n_returns == len(history.dropna()) - 1


def test_stress_chart_starts_at_one_and_names_the_scenario(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """Wealth is normalized to 1.0 on the first actual price date."""
    replay(app, history)
    assert not app.exception and not app.error
    spec = chart_spec(app, "stress_chart")
    assert chart_values(spec["data"][0]["y"])[0] == pytest.approx(1.0)
    assert pd.Timestamp(spec["data"][0]["x"][0]) == history.index[0]
    assert spec["layout"]["title"]["text"] == f"Hypothetical replay · {HISTORICAL_SCENARIOS[1].name}"


def test_switching_scenarios_hides_a_previous_download_error(app: AppTest) -> None:
    """A failed fetch for one crisis is not reported under another crisis."""
    with patch("yfinance.download", side_effect=RuntimeError("timeout")):
        click_button(app, "Run historical stress test")
    assert "timeout" in unavailable(app)
    select(app, "Historical scenario", HISTORICAL_SCENARIOS[0].name)
    assert not app.exception and not app.error
    assert not any("Scenario unavailable" in note.value for note in app.warning)
    assert any("Run the selected scenario" in note.value for note in app.info)


def test_insufficient_history_suggests_a_later_custom_start(
    app: AppTest, history: pd.DataFrame,
) -> None:
    """An unavailable replay explains how to choose a window that can run."""
    history.loc[history.index[:2], "MSFT"] = np.nan
    replay(app, history)
    assert not app.exception and not app.error
    assert "Insufficient history" in unavailable(app)
    assert any("Try a later custom start date" in caption.value for caption in app.caption)
    assert not any(caption.value.startswith("Actual price dates") for caption in app.caption)
